from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480

    sessions_dir: str = "C:/automation_sessions"
    chrome_profiles_dir: str = "C:/chrome-profiles"

    max_concurrent_workers: int = 10

    # CRITICAL: Use absolute paths so API and worker use same databases
    # regardless of which directory they're run from
    database_path: str = str(Path(__file__).resolve().parent.parent / "jobs.db")
    queue_database_path: str = str(Path(__file__).resolve().parent.parent / "jobs_queue.db")

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# Ensure directories exist
Path(settings.sessions_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chrome_profiles_dir).mkdir(parents=True, exist_ok=True)
