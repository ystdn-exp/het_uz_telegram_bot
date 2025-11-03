import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.tasks import jobs
from src.core.config import settings


logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


SCHEDULER_JOBS = {
    "daily_task": {"trigger": CronTrigger(hour=10, minute=0), "id": "daily_task"},
}


def init_scheduler():
    """
    Dynamically gather all jobs declared in scheduler jobs constant.
    """

    for name, parameters in SCHEDULER_JOBS.items():
        job_function = getattr(jobs, name, None)

        if job_function is None:
            raise ImportError(f"Cannot find function {name} in the module.")

        scheduler.add_job(
            job_function, trigger=parameters.get("trigger"), id=parameters.get("id")
        )

    scheduler.start()
