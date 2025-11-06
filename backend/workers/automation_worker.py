"""
Huey worker entry point.
Run this script to start background job processing.
Usage: python workers/automation_worker.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from core.queue import huey
from core.config import settings
import logging

# CRITICAL: Import tasks module to register tasks with Huey
from workers import tasks

logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting Huey worker for automation jobs...")
    logger.info(f"Queue database: {settings.queue_database_path}")
    logger.info(f"Sessions directory: {settings.sessions_dir}")

    # Log registered tasks
    task_names = [name for name in dir(tasks) if not name.startswith('_')]
    logger.info(f"Registered tasks: {task_names}")

    from huey.consumer import Consumer

    consumer = Consumer(huey)
    consumer.run()
