"""Scheduler service for background retention policy execution."""

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Management of background scheduled tasks with APScheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._is_running = False

    def start(self) -> None:
        """Start background scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop background scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped")

    def schedule_policy_execution(
        self,
        func,
        hour: int = 2,
        minute: int = 0,
        job_id: str = "retention_policy_execution",
    ) -> None:
        """Schedule daily retention policy execution.

        Args:
            func: Function to execute
            hour: Hour of day (24-hour format)
            minute: Minute of hour
            job_id: Unique job identifier
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name="Retention Policy Execution",
            replace_existing=True,
        )
        logger.info(f"Scheduled policy execution at {hour:02d}:{minute:02d} daily")

    def schedule_audit_cleanup(
        self,
        func,
        hour: int = 3,
        minute: int = 0,
        job_id: str = "audit_cleanup",
    ) -> None:
        """Schedule audit trail cleanup (archival of old entries).

        Args:
            func: Cleanup function
            hour: Hour of day
            minute: Minute of hour
            job_id: Unique job identifier
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name="Audit Trail Cleanup",
            replace_existing=True,
        )
        logger.info(f"Scheduled audit cleanup at {hour:02d}:{minute:02d} daily")

    def add_job(
        self,
        func,
        trigger,
        job_id: str,
        name: str,
        **kwargs,
    ) -> None:
        """Add custom scheduled job.

        Args:
            func: Function to execute
            trigger: APScheduler trigger (CronTrigger, IntervalTrigger, etc.)
            job_id: Unique job identifier
            name: Human-readable job name
            **kwargs: Additional arguments for add_job
        """
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name,
            **kwargs,
        )
        logger.info(f"Scheduled job '{name}' with ID '{job_id}'")

    def remove_job(self, job_id: str) -> bool:
        """Remove scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was removed, False if not found
        """
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job '{job_id}'")
            return True
        return False

    def get_job(self, job_id: str):
        """Get job by ID."""
        return self.scheduler.get_job(job_id)

    def get_jobs(self) -> list:
        """Get all scheduled jobs."""
        return self.scheduler.get_jobs()

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running
