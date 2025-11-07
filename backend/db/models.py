from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "admin" or "user"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    runs = relationship("Run", back_populates="user", foreign_keys="Run.user_id")


class Run(Base):
    """Automation run model (replaces audit_trail.json entries)"""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "run_20251106_140717"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for scheduled runs
    type = Column(String(50), nullable=False)  # "manual", "scheduled_weekly", "scheduled_monthly"
    status = Column(String(20), nullable=False, default="running")  # "running", "completed", "failed"

    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    # Date range from user input
    start_date = Column(String(20), nullable=False)  # YYYY-MM-DD format
    end_date = Column(String(20), nullable=False)    # YYYY-MM-DD format

    max_clients = Column(Integer, nullable=False, default=10)
    clients_processed = Column(Integer, nullable=False, default=0)

    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)

    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="runs", foreign_keys=[user_id])
    logs = relationship("Log", back_populates="run", cascade="all, delete-orphan")


class Log(Base):
    """
    Automation log entries (one-to-many with Run)
    Separated from Run for better performance with large log volumes
    """
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message = Column(Text, nullable=False)

    # Relationships
    run = relationship("Run", back_populates="logs")


class Schedule(Base):
    """
    Scheduler configuration (single row table)
    Replaces schedule_config.json
    """
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, default=1)  # Always 1

    weekly_enabled = Column(Boolean, default=False, nullable=False)
    weekly_day = Column(Integer, default=1, nullable=False)  # 0-6 (Monday-Sunday)
    weekly_hour = Column(Integer, default=9, nullable=False)  # 0-23
    weekly_minute = Column(Integer, default=0, nullable=False)  # 0-59

    monthly_enabled = Column(Boolean, default=False, nullable=False)
    monthly_day = Column(Integer, default=1, nullable=False)  # 1-28 (day of month)
    monthly_hour = Column(Integer, default=9, nullable=False)  # 0-23
    monthly_minute = Column(Integer, default=0, nullable=False)  # 0-59

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Which admin updated it

    # Relationship
    updated_by_user = relationship("User", foreign_keys=[updated_by])
