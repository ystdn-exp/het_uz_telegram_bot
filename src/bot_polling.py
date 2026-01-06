import asyncio
import logging

from src.bot.bot import bot, dp
from src.core.logging_config import init_logging


async def main():
    init_logging()
    logging.info("Starting bot in polling mode...")

    # Delete webhook if it exists to allow polling
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
