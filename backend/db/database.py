from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Determine database path relative to backend directory
backend_dir = Path(__file__).resolve().parent.parent
DATABASE_PATH = backend_dir / "generations_automation.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine with settings optimized for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threading
        "timeout": 30  # 30 second timeout for locked database
    },
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query debugging
)

# Enable WAL mode and optimize SQLite for concurrent access
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for production use on every connection"""
    cursor = dbapi_conn.cursor()

    # Enable Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")

    # Faster commits, still safe for most use cases
    cursor.execute("PRAGMA synchronous=NORMAL")

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")

    # Increase cache size (negative value = KB, 64MB cache)
    cursor.execute("PRAGMA cache_size=-64000")

    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Dependency function for FastAPI routes.
    Yields a database session and ensures it's closed after use.

    Usage in FastAPI:
        @app.get("/api/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database by creating all tables.
    Call this once during application startup.
    """
    from db import models  # Import models to register them with Base
    Base.metadata.create_all(bind=engine)
