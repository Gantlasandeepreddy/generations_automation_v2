from pydantic_settings import BaseSettings
from pathlib import Path
import secrets


class Settings(BaseSettings):
    # Generations IDB credentials
    generations_agency_id: str
    generations_email: str
    generations_password: str

    # Database settings
    database_url: str = str(Path(__file__).resolve().parent.parent / "generations_automation.db")

    # JWT Authentication settings
    jwt_secret_key: str = secrets.token_urlsafe(32)  # Auto-generate if not in .env
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 1  # 1 day for security (was 7)

    # Session management (relative to project root by default)
    sessions_dir: str = str(Path(__file__).resolve().parent.parent.parent / "automation_sessions")
    chrome_profiles_dir: str = str(Path(__file__).resolve().parent.parent.parent / "chrome-profiles")
    downloads_dir: str = str(Path(__file__).resolve().parent.parent.parent / "downloads")

    # Legacy JSON storage (kept for migration purposes, will be replaced by database)
    audit_file: str = str(Path(__file__).resolve().parent.parent / "audit_trail.json")
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

# Database will be initialized separately via init_db() in main.py
