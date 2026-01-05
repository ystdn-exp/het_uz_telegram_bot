"""
Language selection handler.
"""

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import TelegramUser
from src.bot.keyboards.reply import get_main_menu_keyboard, get_language_keyboard
from src.bot.keyboards.constants import (
    BTN_LANG_EN,
    BTN_LANG_RU,
    BTN_LANG_UZ,
    BTN_CHANGE_LANGUAGE,
)
from src.bot.utils.context_variables import set_locale, i18n

router = Router()


@router.message(F.text == BTN_CHANGE_LANGUAGE)
async def show_language_menu(message: Message, _):
    """
    Show language selection menu when user taps Change Language button.
    """
    await message.answer(
        _("🌐 <b>Select Your Language</b>\n\nChoose your preferred language:"),
        reply_markup=get_language_keyboard(),
    )


@router.message(F.text.in_({BTN_LANG_EN, BTN_LANG_RU, BTN_LANG_UZ}))
async def language_selection(message: Message, session: AsyncSession):
    """
    Handle language selection.
    """
    # Map button text to language code
    lang_map = {
        BTN_LANG_EN: "en",
        BTN_LANG_RU: "ru",
        BTN_LANG_UZ: "uz",
    }

    selected_lang = lang_map.get(message.text)

    # Fetch the user to ensure consistency and handle potential missing user
    user_id = str(message.from_user.id)
    result = await session.execute(
        select(TelegramUser).where(TelegramUser.chat_id == user_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Update user language in database
        if existing_user.language != selected_lang:
            existing_user.language = selected_lang
            await session.commit()
            await session.refresh(existing_user)
    else:
        # Fallback: create user if not exists (should already exist due to /start)
        pass

    # Update current locale context for the current thread/task
    set_locale(selected_lang)

    # Get immediate translation function for the NEWLY selected language
    # This ensures the response below is in the new language
    _ = i18n.get_translations(selected_lang).gettext

    # Success message using immediate translation
    # Wrap in str() to ensure Pydantic doesn't receive a lazy object if babel returns one
    await message.answer(
        _(
            "🌟 <b>Welcome to HET Bot!</b> 🏠✨\n\n"
            "⚡️ Here you can effortlessly manage your electricity accounts and track your consumption! 📉💡\n\n"
            "🚀 Let's get started! Use the menu below to navigate. 👇"
        ),
        reply_markup=get_main_menu_keyboard(),
    )
