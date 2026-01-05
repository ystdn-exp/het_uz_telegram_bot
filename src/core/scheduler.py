import logging

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.tasks import jobs
from src.core.config import settings


logger = logging.getLogger(__name__)

# initialize scheduler instance along with redis cache
jobstores = {
    "default": RedisJobStore(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
}
scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE, jobstores=jobstores)


# apscheduler jobs should be declared in dict
SCHEDULER_JOBS = {
    "daily_task": {"trigger": CronTrigger(hour=10, minute=0), "id": "daily_task"},
    "check_low_balances_task": {
        "trigger": "interval",
        "minutes": 50,
        "id": "check_low_balances_task",
    },
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

    return scheduler


def shutdown_scheduler():
    """Disable schuduler."""
    scheduler.shutdown(wait=False)
