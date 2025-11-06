from huey import SqliteHuey
from core.config import settings

huey = SqliteHuey(
    filename=settings.queue_database_path,
    immediate=False,
    utc=True,
    results=True,
    store_none=False
)
