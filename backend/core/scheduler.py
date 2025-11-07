from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db.database import SessionLocal
from db import crud
import logging

logger = logging.getLogger(__name__)


class AutomationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def get_config(self) -> Dict[str, Any]:
        """Read scheduler configuration from database."""
        db = SessionLocal()
        try:
            return crud.get_schedule_as_dict(db)
        finally:
            db.close()

    def update_schedule(self, config: Dict[str, Any], automation_callback):
        """Update the scheduler with new configuration."""
        # Note: config is already saved to database in main.py
        # This method only updates the APScheduler jobs

        # Remove existing jobs
        self.scheduler.remove_all_jobs()

        # Add weekly job if enabled
        if config.get("weekly_enabled", False):
            weekly_trigger = CronTrigger(
                day_of_week=config.get("weekly_day", 1),
                hour=config.get("weekly_hour", 9),
                minute=config.get("weekly_minute", 0)
            )

            # Calculate weekly date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            self.scheduler.add_job(
                automation_callback,
                trigger=weekly_trigger,
                args=[{
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }, "weekly"],
                id="weekly_automation",
                name="Weekly Automation",
                replace_existing=True
            )
            logger.info(f"Scheduled weekly automation: Day {config.get('weekly_day')} at {config.get('weekly_hour')}:{config.get('weekly_minute')}")

        # Add monthly job if enabled
        if config.get("monthly_enabled", False):
            monthly_trigger = CronTrigger(
                day=config.get("monthly_day", 1),
                hour=config.get("monthly_hour", 9),
                minute=config.get("monthly_minute", 0)
            )

            # Calculate monthly date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            self.scheduler.add_job(
                automation_callback,
                trigger=monthly_trigger,
                args=[{
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }, "monthly"],
                id="monthly_automation",
                name="Monthly Automation",
                replace_existing=True
            )
            logger.info(f"Scheduled monthly automation: Day {config.get('monthly_day')} at {config.get('monthly_hour')}:{config.get('monthly_minute')}")

    def start(self, automation_callback):
        """Start the scheduler with current configuration."""
        config = self.get_config()
        self.update_schedule(config, automation_callback)

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")


automation_scheduler = AutomationScheduler()
