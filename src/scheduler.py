import asyncio
import logging

from src.core.scheduler import scheduler, init_scheduler


# Configure logging for the standalone process
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("scheduler_process")


async def main():
    logger.info("Starting standalone scheduler process...")

    init_scheduler()

    logger.info("Scheduler is running. Press Ctrl+C to exit.")

    try:
        # Keep the process alive
        while True:
            await asyncio.sleep(1000)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
