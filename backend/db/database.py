import sqlite3
from core.config import settings
from pathlib import Path


def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            date_range_start TEXT,
            date_range_end TEXT,
            total_clients INTEGER DEFAULT 0,
            processed_clients INTEGER DEFAULT 0,
            failed_clients INTEGER DEFAULT 0,
            json_file_path TEXT,
            excel_file_path TEXT,
            error_message TEXT,
            logs TEXT DEFAULT ''
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON jobs(user_email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)')

    conn.commit()
    conn.close()


# Initialize database on module import
init_database()
