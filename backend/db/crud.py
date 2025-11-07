from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from db import models
from core.auth import get_password_hash, validate_password


# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_user(db: Session, email: str, password: str, role: str = "user") -> models.User:
    """Create a new user with hashed password"""
    # Validate password complexity
    validate_password(password)

    password_hash = get_password_hash(password)
    user = models.User(
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email address"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_all_users(db: Session, include_inactive: bool = False) -> List[models.User]:
    """Get all users, optionally including inactive ones"""
    query = db.query(models.User)
    if not include_inactive:
        query = query.filter(models.User.is_active == True)
    return query.order_by(models.User.created_at.desc()).all()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[models.User]:
    """
    Update user fields.
    Allowed fields: email, role, is_active, password (will be hashed)
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    # Validate and hash password if provided
    if 'password' in kwargs:
        validate_password(kwargs['password'])
        kwargs['password_hash'] = get_password_hash(kwargs.pop('password'))

    # Update allowed fields
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """Soft delete user (set is_active=False)"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    return True


def hard_delete_user(db: Session, user_id: int) -> bool:
    """Permanently delete user from database"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


# ============================================================================
# RUN OPERATIONS (Replaces audit_trail.py functionality)
# ============================================================================

def create_run(db: Session, run_type: str, date_range: Dict[str, str],
               max_clients: int, user_id: Optional[int] = None) -> models.Run:
    """
    Create a new automation run entry.
    Returns the created Run object.
    """
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    run = models.Run(
        run_id=run_id,
        user_id=user_id,
        type=run_type,
        status="running",
        start_time=datetime.utcnow(),
        start_date=date_range.get("start_date", ""),
        end_date=date_range.get("end_date", ""),
        max_clients=max_clients,
        clients_processed=0
    )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run_by_run_id(db: Session, run_id: str) -> Optional[models.Run]:
    """Get run by run_id string (e.g., 'run_20251106_140717')"""
    return db.query(models.Run).filter(models.Run.run_id == run_id).first()


def get_run_by_id(db: Session, id: int) -> Optional[models.Run]:
    """Get run by database ID"""
    return db.query(models.Run).filter(models.Run.id == id).first()


def delete_run(db: Session, run_id: str) -> bool:
    """
    Delete a run and all associated logs from the database.
    Returns True if successful, False if run not found.
    """
    run = get_run_by_run_id(db, run_id)
    if not run:
        return False

    # Delete run (logs will be deleted automatically via cascade)
    db.delete(run)
    db.commit()
    return True


def get_all_runs(db: Session, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all automation runs with user info and logs.
    Returns runs sorted by start_time descending (newest first).
    Matches the structure of old audit_trail.json
    """
    runs = db.query(models.Run).options(
        joinedload(models.Run.user),
        joinedload(models.Run.logs)
    ).order_by(models.Run.start_time.desc()).limit(limit).all()

    result = []
    for run in runs:
        run_dict = {
            "run_id": run.run_id,
            "type": run.type,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "date_range": {
                "start_date": run.start_date,
                "end_date": run.end_date
            },
            "max_clients": run.max_clients,
            "clients_processed": run.clients_processed,
            "logs": [log.message for log in sorted(run.logs, key=lambda x: x.timestamp)],
            "file_path": run.file_path,
            "file_size": run.file_size,
            "error": run.error,
            "user_email": run.user.email if run.user else "System"
        }
        result.append(run_dict)

    return result


def append_log(db: Session, run_id: str, message: str):
    """Add a log message to a run"""
    run = get_run_by_run_id(db, run_id)
    if not run:
        return

    log = models.Log(
        run_id=run.id,
        timestamp=datetime.utcnow(),
        message=message
    )

    db.add(log)
    db.commit()


def get_logs_for_run(db: Session, run_db_id: int) -> List[models.Log]:
    """Get all logs for a run (ordered by timestamp)"""
    return db.query(models.Log).filter(
        models.Log.run_id == run_db_id
    ).order_by(models.Log.timestamp.asc()).all()


def update_progress(db: Session, run_id: str, clients_processed: int):
    """Update the number of clients processed"""
    run = get_run_by_run_id(db, run_id)
    if not run:
        return

    run.clients_processed = clients_processed
    db.commit()


def complete_run(db: Session, run_id: str, file_path: Optional[str] = None,
                 error: Optional[str] = None):
    """Mark a run as completed or failed"""
    run = get_run_by_run_id(db, run_id)
    if not run:
        return

    run.end_time = datetime.utcnow()
    run.status = "failed" if error else "completed"

    if file_path:
        run.file_path = file_path
        if Path(file_path).exists():
            run.file_size = Path(file_path).stat().st_size

    if error:
        run.error = error

    db.commit()


def get_run_with_logs(db: Session, run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single run with all its logs.
    Used for SSE streaming during automation.
    """
    run = db.query(models.Run).options(
        joinedload(models.Run.logs),
        joinedload(models.Run.user)
    ).filter(models.Run.run_id == run_id).first()

    if not run:
        return None

    return {
        "run_id": run.run_id,
        "status": run.status,
        "logs": [log.message for log in sorted(run.logs, key=lambda x: x.timestamp)],
        "file_path": run.file_path,
        "error": run.error
    }


# ============================================================================
# SCHEDULE OPERATIONS (Replaces schedule_config.json)
# ============================================================================

def get_schedule(db: Session) -> Optional[models.Schedule]:
    """Get the schedule configuration (single row table)"""
    schedule = db.query(models.Schedule).filter(models.Schedule.id == 1).first()

    # Create default schedule if doesn't exist
    if not schedule:
        schedule = models.Schedule(
            id=1,
            weekly_enabled=False,
            weekly_day=1,
            weekly_hour=9,
            weekly_minute=0,
            monthly_enabled=False,
            monthly_day=1,
            monthly_hour=9,
            monthly_minute=0
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

    return schedule


def update_schedule(db: Session, config: Dict[str, Any], updated_by: Optional[int] = None) -> models.Schedule:
    """Update schedule configuration"""
    schedule = get_schedule(db)

    # Update fields
    for key, value in config.items():
        if hasattr(schedule, key):
            setattr(schedule, key, value)

    schedule.updated_at = datetime.utcnow()
    if updated_by:
        schedule.updated_by = updated_by

    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule_as_dict(db: Session) -> Dict[str, Any]:
    """Get schedule configuration as dictionary (matches old JSON format)"""
    schedule = get_schedule(db)

    return {
        "weekly_enabled": schedule.weekly_enabled,
        "weekly_day": schedule.weekly_day,
        "weekly_hour": schedule.weekly_hour,
        "weekly_minute": schedule.weekly_minute,
        "monthly_enabled": schedule.monthly_enabled,
        "monthly_day": schedule.monthly_day,
        "monthly_hour": schedule.monthly_hour,
        "monthly_minute": schedule.monthly_minute
    }
