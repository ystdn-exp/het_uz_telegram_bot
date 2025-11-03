from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware, types

from src.bot.utils.context_variables import set_locale
from src.database.repositories.users import TelegramUserRepository


class LocaleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Update, Dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        lang = TelegramUserRepository.get_preferred_language(user_id, "en")
        set_locale(lang)
        return await handler(event, data)


# NOTE: need to register the middleware
# bot/bot.py
# from bot.middlewares import LocaleMiddleware

# dp.message.middleware(LocaleMiddleware())
# dp.callback_query.middleware(LocaleMiddleware())
