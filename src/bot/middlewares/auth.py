from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.users import TelegramUserService


class AuthMiddleware(BaseMiddleware):
    """
    Middleware to ensure Telegram user exists in the database.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Get session from data (provided by DbSessionMiddleware)
        session: AsyncSession = data.get("session")

        # Get user from event
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        elif event.inline_query:
            user = event.inline_query.from_user

        if user and session:
            # Ensure user exists in database
            await TelegramUserService.get_or_create_user(
                session,
                chat_id=str(user.id),
                username=user.username,
                language=user.language_code or "en",
            )

        return await handler(event, data)
