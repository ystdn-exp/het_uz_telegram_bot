import logging


logger = logging.getLogger(__name__)


async def daily_task():
    logger.info("Running daily task")
