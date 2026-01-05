"""
Start command handler.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.reply import get_language_keyboard


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, _):
    """
    Handle /start command - welcome users and create TelegramUser if needed.

    Args:
        message: Incoming message
        session: Database session
        _: Translation function from middleware
    """

    # Ask for language preference first (immediate translation)
    await message.answer(
        _(
            "Please select your language / Пожалуйста, выберите язык / Iltimos, tilni tanlang:"
        ),
        reply_markup=get_language_keyboard(),
    )
