"""
Registration handler for adding HET accounts.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.exceptions import ValidationError
from src.bot.keyboards.constants import BTN_ADD_ACCOUNT
from src.bot.keyboards.reply import get_main_menu_keyboard, get_remove_keyboard
from src.bot.states.registration import RegistrationStates
from src.services.users import TelegramUserService

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == BTN_ADD_ACCOUNT)
async def start_registration(
    message: Message, state: FSMContext, session: AsyncSession, _
):
    """
    Start HET account registration flow.

    Args:
        message: Incoming message
        state: FSM state context
        session: Database session
        _: Translation function
    """
    # Check if user already has 3 accounts (max limit)
    telegram_user = await TelegramUserService.get_user(
        session, chat_id=str(message.from_user.id)
    )

    if telegram_user and len(telegram_user.users) >= 3:
        await message.answer(
            _(
                "🚫 <b>Limit Reached</b>\n\n"
                "You have reached the maximum limit of 3 linked accounts.\n"
                "To add a new one, please remove an existing account first."
            ),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Start registration flow
    await state.set_state(RegistrationStates.waiting_for_username)
    await message.answer(
        _("👤 <b>Username Required</b>\n\nPlease enter your HET account username:"),
        reply_markup=get_remove_keyboard(),
    )


@router.message(RegistrationStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext, _):
    """
    Process HET username and request password.

    Args:
        message: Incoming message with username
        state: FSM state context
        _: Translation function
    """
    username = message.text.strip()

    if not username:
        await message.answer(
            _("⚠️ <b>Invalid Username</b>\n\nUsername cannot be empty. Please try again:")
        )
        return

    # Store username in FSM context
    await state.update_data(username=username)

    # Move to next state
    await state.set_state(RegistrationStates.waiting_for_password)
    await message.answer(
        _(
            "🔐 <b>Password Required</b>\n\nGreat! Now please enter your HET account password:"
        )
    )


@router.message(RegistrationStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext, session: AsyncSession, _):
    """
    Process password, validate with HET API, and save account.

    Args:
        message: Incoming message with password
        state: FSM state context
        session: Database session
        _: Translation function
    """
    password = message.text.strip()

    if not password:
        await message.answer(
            _("⚠️ <b>Invalid Password</b>\n\nPassword cannot be empty. Please try again:")
        )
        return

    # Get username from FSM context
    data = await state.get_data()
    username = data.get("username")

    # Delete the password message for security
    try:
        await message.delete()
    except Exception:
        pass  # Ignore if we can't delete (e.g., not enough permissions)

    # Show processing message
    processing_msg = await message.answer(
        _("🔄 <b>Verifying Credentials...</b>\nPlease wait while we check your details.")
    )

    try:
        # Add user account (this validates with HET API)
        await TelegramUserService.add_user(
            session,
            chat_id=str(message.from_user.id),
            client=message.bot.session_client,
            het_username=username,
            het_password=password,
        )

        # Clear FSM state
        await state.clear()

        # Delete processing message
        await processing_msg.delete()

        # Success message
        await message.answer(
            _(
                "🎉 <b>Success!</b>\n\n"
                "Account has been successfully linked!\n"
                "👤 <b>Username:</b> {username}\n\n"
                "You can now track your electricity consumption statistics effortlessly 📉"
            ).format(username=username),
            reply_markup=get_main_menu_keyboard(),
        )

    except ValidationError as e:
        # Clear FSM state
        await state.clear()

        # Delete processing message
        await processing_msg.delete()

        # Show error
        await message.answer(
            _(
                "❌ <b>Authentication Failed</b>\n\n"
                "{error}\n\n"
                "Please check your credentials and try again."
            ).format(error=str(e)),
            reply_markup=get_main_menu_keyboard(),
        )

    except Exception as e:
        logger.exception(
            f"Unexpected error during registration for user {message.from_user.id}: {e}"
        )
        # Clear FSM state
        await state.clear()

        # Delete processing message
        try:
            await processing_msg.delete()
        except Exception:
            pass

        # Generic error
        await message.answer(
            _("❌ An unexpected error occurred. Please try again later."),
            reply_markup=get_main_menu_keyboard(),
        )
