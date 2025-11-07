import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, AsyncIterator, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.scheduler import automation_scheduler
from core.session_manager import GenerationsSession
from core.auth import get_current_user, require_admin, initialize_secret_key
from db.database import get_db, init_db, SessionLocal
from db import crud, models
from db.audit import audit_trail

from automation.selenium_helpers import build_driver
from automation.report_automation import login_and_open_report_writer, export_single_report, find_client_notes_report
from automation.client_search import process_clients_from_json
from automation.mapping_excel import generate_excel_from_json

# Import API routers
from api import auth, users

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models
class AutomationRequest(BaseModel):
    start_date: str
    end_date: str
    max_clients: int = 10


class ScheduleConfig(BaseModel):
    weekly_enabled: bool = False
    weekly_day: int = 1
    weekly_hour: int = 9
    weekly_minute: int = 0
    monthly_enabled: bool = False
    monthly_day: int = 1
    monthly_hour: int = 9
    monthly_minute: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

    logger.info("Initializing JWT secret key...")
    initialize_secret_key(settings.jwt_secret_key)
    logger.info("JWT configured")

    logger.info("Starting automation scheduler...")
    automation_scheduler.start(run_scheduled_automation)
    yield
    logger.info("Shutting down automation scheduler...")
    automation_scheduler.stop()


app = FastAPI(title="Generations Automation", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://172.29.144.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(users.router)


def run_scheduled_automation(date_range: Dict[str, str], run_type: str):
    """Wrapper for scheduled automation runs - processes ALL clients"""
    try:
        logger.info(f"Running scheduled {run_type} automation")

        # Create run in database (scheduled runs have no user_id)
        db = SessionLocal()
        try:
            run = crud.create_run(
                db=db,
                run_type="scheduled_" + run_type,
                date_range=date_range,
                max_clients=0,
                user_id=None  # System-initiated run
            )
            run_id = run.run_id
        finally:
            db.close()

        # Run automation workflow
        run_automation_workflow(run_id, date_range, max_clients=0, run_type="scheduled_" + run_type, user_id=None)

    except Exception as e:
        logger.error(f"Scheduled automation failed: {e}")


def run_automation_workflow(run_id: str, date_range: Dict[str, str], max_clients: int = 10, run_type: str = "manual", user_id: Optional[int] = None):
    """Core automation workflow - used by both scheduled and manual runs"""

    try:
        audit_trail.append_log(run_id, f"Starting {run_type} automation")

        # Setup download directory
        download_dir = Path(settings.sessions_dir) / run_id / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)

        driver = build_driver(download_dir, headless=False)

        credentials = {
            'agency_id': settings.generations_agency_id,
            'email': settings.generations_email,
            'password': settings.generations_password
        }
        session = GenerationsSession(driver, credentials, run_id)

        audit_trail.append_log(run_id, "Logging into Generations IDB...")
        driver = login_and_open_report_writer(
            driver,
            credentials['agency_id'],
            credentials['email'],
            credentials['password']
        )
        session.update_activity()

        audit_trail.append_log(run_id, "Finding Client Notes report...")
        option_value, option_text = find_client_notes_report(driver)
        audit_trail.append_log(run_id, f"Found report: {option_text}")

        # Convert dates from YYYY-MM-DD to MM/DD/YYYY format
        from datetime import datetime as dt
        start_date_obj = dt.strptime(date_range['start_date'], '%Y-%m-%d')
        end_date_obj = dt.strptime(date_range['end_date'], '%Y-%m-%d')
        start_str = start_date_obj.strftime('%m/%d/%Y')
        end_str = end_date_obj.strftime('%m/%d/%Y')

        audit_trail.append_log(run_id, f"Exporting Client Notes report for {start_str} to {end_str}...")
        json_file_path = export_single_report(
            driver=driver,
            download_dir=download_dir,
            option_value=option_value,
            option_text=option_text,
            start_str=start_str,
            end_str=end_str
        )
        session.update_activity()

        audit_trail.append_log(run_id, "Processing client personal data...")
        enriched_json_path = process_clients_from_json(
            driver=driver,
            json_file_path=json_file_path,
            run_id=run_id,
            session=session,
            max_clients=max_clients
        )

        audit_trail.append_log(run_id, "Generating Excel file...")
        # Use the download directory instead of just run_id
        excel_file_path = generate_excel_from_json(enriched_json_path, download_dir)

        final_filename = f"{run_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        final_path = Path(settings.downloads_dir) / final_filename
        Path(excel_file_path).rename(final_path)

        driver.quit()

        audit_trail.complete_run(run_id, file_path=str(final_path))
        audit_trail.append_log(run_id, "Automation completed successfully")

    except Exception as e:
        error_msg = f"Automation failed: {str(e)}\n{traceback.format_exc()}"
        audit_trail.append_log(run_id, error_msg)
        audit_trail.complete_run(run_id, error=error_msg)

        try:
            driver.quit()
        except:
            pass




async def stream_logs(run_id: str) -> AsyncIterator[str]:
    """Stream logs in real-time for a running automation"""
    import asyncio
    import json

    last_log_count = 0

    while True:
        # Get run from database
        db = SessionLocal()
        try:
            run = crud.get_run_with_logs(db, run_id)
        finally:
            db.close()

        if not run:
            yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
            break

        current_logs = run.get("logs", [])
        new_logs = current_logs[last_log_count:]

        for log in new_logs:
            yield f"data: {json.dumps({'log': log})}\n\n"

        last_log_count = len(current_logs)

        if run["status"] in ["completed", "failed"]:
            yield f"data: {json.dumps({'status': run['status'], 'file_path': run.get('file_path', ''), 'run_id': run_id})}\n\n"
            break

        await asyncio.sleep(1)


# API Routes

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "scheduler_running": automation_scheduler.scheduler.running}


@app.post("/api/automation/run")
async def run_automation(
    request: AutomationRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger manual automation and stream logs in real-time.
    Returns Server-Sent Events (SSE) stream.
    Requires authentication.
    """
    import threading

    date_range = {
        "start_date": request.start_date,
        "end_date": request.end_date
    }

    # Create run with user attribution
    run = crud.create_run(
        db=db,
        run_type="manual",
        date_range=date_range,
        max_clients=request.max_clients,
        user_id=current_user.id
    )
    run_id = run.run_id

    thread = threading.Thread(
        target=lambda: run_automation_workflow(
            run_id, date_range, request.max_clients, "manual", current_user.id
        )
    )
    thread.start()

    return StreamingResponse(
        stream_logs(run_id),
        media_type="text/event-stream"
    )


@app.get("/api/automation/history")
def get_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all automation run history (all users see all runs)"""
    runs = crud.get_all_runs(db)
    return {"runs": runs}


@app.get("/api/automation/download/{run_id}")
def download_file(
    run_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download Excel file for a specific run"""
    run = crud.get_run_by_run_id(db, run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    file_path = run.file_path

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(file_path).name
    )


@app.get("/api/automation/logs/{run_id}")
def get_run_logs(
    run_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get logs for a specific automation run"""
    run = crud.get_run_by_run_id(db, run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = crud.get_logs_for_run(db, run.id)

    return {
        "run_id": run.run_id,
        "status": run.status,
        "start_time": run.start_time.isoformat(),
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "message": log.message
            }
            for log in logs
        ]
    }


@app.get("/api/schedule")
def get_schedule(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current schedule configuration"""
    schedule_config = crud.get_schedule_as_dict(db)
    return schedule_config


@app.post("/api/schedule")
def update_schedule(
    config: ScheduleConfig,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update schedule configuration (admin only)"""
    config_dict = config.model_dump()

    # Update in database
    crud.update_schedule(db, config_dict, updated_by=admin.id)

    # Update scheduler
    automation_scheduler.update_schedule(config_dict, run_scheduled_automation)

    return {"message": "Schedule updated successfully", "config": config_dict}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
