from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Generations IDB credentials (single user)
    generations_agency_id: str
    generations_email: str
    generations_password: str

    # Simple UI login credentials
    ui_email: str = "admin@example.com"
    ui_password: str = "changeme"

    # Session management (relative to project root by default)
    sessions_dir: str = str(Path(__file__).resolve().parent.parent.parent / "automation_sessions")
    chrome_profiles_dir: str = str(Path(__file__).resolve().parent.parent.parent / "chrome-profiles")
    downloads_dir: str = str(Path(__file__).resolve().parent.parent.parent / "downloads")

    # Audit trail storage
    audit_file: str = str(Path(__file__).resolve().parent.parent / "audit_trail.json")

    # Scheduler settings
    schedule_config_file: str = str(Path(__file__).resolve().parent.parent / "schedule_config.json")

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# Ensure directories exist
Path(settings.sessions_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chrome_profiles_dir).mkdir(parents=True, exist_ok=True)
Path(settings.downloads_dir).mkdir(parents=True, exist_ok=True)

# Ensure audit file exists
audit_path = Path(settings.audit_file)
if not audit_path.exists():
    audit_path.write_text("[]")

# Ensure schedule config exists
schedule_path = Path(settings.schedule_config_file)
if not schedule_path.exists():
    schedule_path.write_text('{"weekly_enabled": false, "monthly_enabled": false}')
