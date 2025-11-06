import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from core.config import settings


class AuditTrail:
    def __init__(self):
        self.audit_file = Path(settings.audit_file)

    def _read_audit_log(self) -> List[Dict[str, Any]]:
        """Read the audit log from JSON file."""
        if not self.audit_file.exists():
            return []

        try:
            with open(self.audit_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _write_audit_log(self, data: List[Dict[str, Any]]):
        """Write the audit log to JSON file."""
        with open(self.audit_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_run(self, run_type: str, date_range: Dict[str, str], max_clients: int) -> str:
        """Create a new automation run entry and return run_id."""
        audit_log = self._read_audit_log()

        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        entry = {
            "run_id": run_id,
            "type": run_type,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "date_range": date_range,
            "max_clients": max_clients,
            "clients_processed": 0,
            "logs": [],
            "file_path": None,
            "file_size": None,
            "error": None
        }

        audit_log.append(entry)
        self._write_audit_log(audit_log)

        return run_id

    def append_log(self, run_id: str, message: str):
        """Append a log message to a specific run."""
        audit_log = self._read_audit_log()

        for entry in audit_log:
            if entry["run_id"] == run_id:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                entry["logs"].append(f"[{timestamp}] {message}")
                break

        self._write_audit_log(audit_log)

    def update_progress(self, run_id: str, clients_processed: int):
        """Update the number of clients processed."""
        audit_log = self._read_audit_log()

        for entry in audit_log:
            if entry["run_id"] == run_id:
                entry["clients_processed"] = clients_processed
                break

        self._write_audit_log(audit_log)

    def complete_run(self, run_id: str, file_path: Optional[str] = None, error: Optional[str] = None):
        """Mark a run as completed or failed."""
        audit_log = self._read_audit_log()

        for entry in audit_log:
            if entry["run_id"] == run_id:
                entry["end_time"] = datetime.now().isoformat()
                entry["status"] = "failed" if error else "completed"

                if file_path:
                    entry["file_path"] = file_path
                    file_size = Path(file_path).stat().st_size if Path(file_path).exists() else None
                    entry["file_size"] = file_size

                if error:
                    entry["error"] = error

                break

        self._write_audit_log(audit_log)

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all automation runs, sorted by start time descending."""
        audit_log = self._read_audit_log()
        return sorted(audit_log, key=lambda x: x["start_time"], reverse=True)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        audit_log = self._read_audit_log()

        for entry in audit_log:
            if entry["run_id"] == run_id:
                return entry

        return None

    def delete_old_runs(self, keep_count: int = 100):
        """Keep only the most recent runs and delete older entries."""
        audit_log = self._read_audit_log()

        if len(audit_log) <= keep_count:
            return

        sorted_log = sorted(audit_log, key=lambda x: x["start_time"], reverse=True)
        self._write_audit_log(sorted_log[:keep_count])


audit_trail = AuditTrail()
