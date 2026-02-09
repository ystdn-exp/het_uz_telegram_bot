import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.perf_counter()
        user = data.get("event_from_user")
        user_id = user if user.id else "system"

        update_type = event.__class__.__name__

        if logger.isEnabledFor(logging.DEBUG):
            update = data.get("event_update")
            if update:
                logger.debug(f"Raw Update: {update.model_dump_json(indent=2)}")

        try:
            result = await handler(event, data)
            duration = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"Update: {update_type} | User: {user_id} | "
                f"Duration: {duration:.2f}ms | Status: Success"
            )

            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Update: {update_type} | User: {user_id} | "
                f"Duration: {duration:.2f}ms | Status: Error | "
                f"Error: {e}",
                exc_info=True,  # This includes the stack trace
            )
            # Re-raise so aiogram's error handlers can catch it too
            raise
