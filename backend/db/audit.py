"""
Database-backed audit trail for automation runs.
Maintains same interface as legacy JSON-based implementation for backward compatibility.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from db.database import SessionLocal
from db import crud


class AuditTrail:
    """
    Database-backed audit trail.
    All methods maintain the same interface as the legacy JSON implementation.
    """

    def append_log(self, run_id: str, message: str):
        """Append a log message to a specific run."""
        db = SessionLocal()
        try:
            # Format message with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            crud.append_log(db, run_id, formatted_message)
        finally:
            db.close()

    def update_progress(self, run_id: str, clients_processed: int):
        """Update the number of clients processed."""
        db = SessionLocal()
        try:
            crud.update_progress(db, run_id, clients_processed)
        finally:
            db.close()

    def complete_run(self, run_id: str, file_path: Optional[str] = None, error: Optional[str] = None):
        """Mark a run as completed or failed."""
        db = SessionLocal()
        try:
            crud.complete_run(db, run_id, file_path=file_path, error=error)
        finally:
            db.close()

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all automation runs, sorted by start time descending."""
        db = SessionLocal()
        try:
            return crud.get_all_runs(db)
        finally:
            db.close()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        db = SessionLocal()
        try:
            return crud.get_run_with_logs(db, run_id)
        finally:
            db.close()


audit_trail = AuditTrail()
