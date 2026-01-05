from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.bot.utils.context_variables import set_locale, i18n
from src.services.users import TelegramUserService


class LocaleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")

        if user:
            session = data.get("session")
            lang = await TelegramUserService.get_user_language(session, str(user.id))
            print(f"DEBUG: LocaleMiddleware setting lang to: {lang} for user {user.id}")
            set_locale(lang)
        else:
            lang = "en"

        data["_"] = i18n.get_translations(lang).gettext

        return await handler(event, data)
