from datetime import datetime
from db.database import get_db_connection


def create_job(job_id: str, user_email: str, date_range_start: str, date_range_end: str):
    """Create new job record"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO jobs (job_id, user_email, status, date_range_start, date_range_end)
        VALUES (?, ?, ?, ?, ?)
    ''', (job_id, user_email, 'queued', date_range_start, date_range_end))

    conn.commit()
    conn.close()


def get_job(job_id: str):
    """Get job by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def update_job_status(job_id: str, status: str):
    """Update job status"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if status == 'processing':
        cursor.execute('''
            UPDATE jobs SET status = ?, started_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        ''', (status, job_id))
    else:
        cursor.execute('UPDATE jobs SET status = ? WHERE job_id = ?', (status, job_id))

    conn.commit()
    conn.close()


def update_job_clients(job_id: str, total: int, processed: int, failed: int):
    """Update job client counts"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE jobs
        SET total_clients = ?, processed_clients = ?, failed_clients = ?
        WHERE job_id = ?
    ''', (total, processed, failed, job_id))

    conn.commit()
    conn.close()


def append_log(job_id: str, message: str):
    """Append log message to job"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT logs FROM jobs WHERE job_id = ?', (job_id,))
    row = cursor.fetchone()

    if row:
        current_logs = row['logs'] or ''
        new_logs = current_logs + log_entry

        cursor.execute('UPDATE jobs SET logs = ? WHERE job_id = ?', (new_logs, job_id))
        conn.commit()

    conn.close()


def complete_job(job_id: str, json_file_path: str, excel_file_path: str):
    """Mark job as completed"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE jobs
        SET status = 'completed',
            completed_at = CURRENT_TIMESTAMP,
            json_file_path = ?,
            excel_file_path = ?
        WHERE job_id = ?
    ''', (json_file_path, excel_file_path, job_id))

    conn.commit()
    conn.close()


def fail_job(job_id: str, error_message: str):
    """Mark job as failed"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE jobs
        SET status = 'failed',
            completed_at = CURRENT_TIMESTAMP,
            error_message = ?
        WHERE job_id = ?
    ''', (error_message, job_id))

    conn.commit()
    conn.close()


def get_user_jobs(user_email: str, limit: int = 50):
    """Get all jobs for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM jobs
        WHERE user_email = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_email, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
