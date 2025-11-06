import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class AutomationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.config_file = Path(settings.schedule_config_file)

    def get_config(self) -> Dict[str, Any]:
        """Read scheduler configuration from JSON file."""
        if not self.config_file.exists():
            return {
                "weekly_enabled": False,
                "weekly_day": 1,  # Monday
                "weekly_hour": 9,
                "weekly_minute": 0,
                "monthly_enabled": False,
                "monthly_day": 1,  # 1st of month
                "monthly_hour": 9,
                "monthly_minute": 0
            }

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"weekly_enabled": False, "monthly_enabled": False}

    def save_config(self, config: Dict[str, Any]):
        """Save scheduler configuration to JSON file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def update_schedule(self, config: Dict[str, Any], automation_callback):
        """Update the scheduler with new configuration."""
        self.save_config(config)

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
