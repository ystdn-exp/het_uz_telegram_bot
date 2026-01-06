"""
User account management handlers and callbacks.
"""

from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handlers.utils import (
    _format_payments_history,
    _get_account_link,
    _process_yearly_data,
    process_chart_data,
)
from src.bot.keyboards.constants import (
    BTN_HELP,
    BTN_MY_ACCOUNTS,
    CB_BACK,
    CB_CANCEL,
    CB_CONFIRM_DELETE,
    CB_DELETE,
    CB_PAYMENTS,
    CB_PERIOD,
    CB_READINGS,
    CB_SELECT_YEAR,
    CB_SWITCH_PERIOD,
    CB_VIEW_ACCOUNT,
)
from src.bot.keyboards.inline import (
    get_accounts_keyboard,
    get_confirm_keyboard,
    get_period_keyboard,
    get_stats_keyboard,
    get_year_selection_keyboard,
)
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.services.charts import ChartService
from src.services.het import het_service
from src.services.users import TelegramUserService

router = Router()


@router.message(F.text == BTN_MY_ACCOUNTS)
async def show_accounts(message: Message, session: AsyncSession, _):
    """
    Show list of user's HET accounts.

    Args:
        message: Incoming message
        session: Database session
        _: Translation function
    """
    telegram_user = await TelegramUserService.get_user(
        session, chat_id=str(message.from_user.id)
    )

    if not telegram_user or not telegram_user.users:
        await message.answer(
            _(
                "📭 <b>No Accounts Linked</b>\n\n"
                "You haven't linked any HET accounts yet.\n"
                "Tap <b>'➕ Add Account'</b> below to get started and track your usage!"
            ),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Build accounts list
    accounts = [
        {"id": str(link.user.id), "username": link.user.username}
        for link in telegram_user.users
    ]

    await message.answer(
        _(
            "📋 <b>Your HET Accounts</b>\n\nSelect an account below to view detailed statistics and consumption data:"
        ),
        reply_markup=get_accounts_keyboard(accounts),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def help_command(message: Message, _):
    """
    Show help information.

    Args:
        message: Incoming message
        _: Translation function
    """
    help_text = str(
        _(
            "🤖 <b>HET Bot Assistance</b>\n\n"
            "Here's how I can help you manage your electricity data:\n\n"
            "<b>📂 Account Management</b>\n"
            "• <b>➕ Add Account:</b> Link up to 3 HET electricity accounts.\n"
            "• <b>👁 My Accounts:</b> View linked accounts, check balances & statistics.\n\n"
            "<b>📊 Statistics & Tracking</b>\n"
            "View detailed consumption graphs for:\n"
            "• 🗓 Monthly\n"
            "• 📅 Yearly\n\n"
            "• 📑 Meter Readings & Payments History\n\n"
            "<b>🔔 Notifications</b>\n"
            "I'll send you a daily summary of your electricity usage at 10:00 AM.\n\n"
            "<b>🆘 Support</b>\n"
            "Need more help? Contact your system administrator."
        )
    )

    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data.startswith(CB_VIEW_ACCOUNT))
async def view_account_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    View account details and show period selection.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    # Parse account_id from callback data
    try:
        account_id = UUID(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(_("❌ Invalid account"), show_alert=True)
        return

    # Get account details
    telegram_user = await TelegramUserService.get_user(
        session, chat_id=str(callback.from_user.id)
    )

    # Find the specific account
    account_link = _get_account_link(telegram_user, account_id)

    if not account_link:
        await callback.answer(_("❌ Account not found"), show_alert=True)
        return

    username = account_link.user.username
    access_token = account_link.access_token
    balance_text = ""

    # Fetch consumer state for balance
    data, status = await het_service.get_consumer_state(callback.bot.session_client, access_token)

    # Handle expired token
    if status == 401 and account_link.refresh_token:
        new_tokens, refresh_status = await het_service.refresh_token(
            callback.bot.session_client, account_link.refresh_token
        )
        if refresh_status == 200 and new_tokens.get("data"):
            tokens = new_tokens["data"]
            account_link.access_token = tokens.get("accessToken")
            account_link.refresh_token = tokens.get("refreshToken")
            session.add(account_link)
            await session.commit()
            access_token = account_link.access_token
            # Retry fetch
            data, status = await het_service.get_consumer_state(
                callback.bot.session_client, access_token
            )

    if status == 200 and data.get("data"):
        balance = data["data"].get("balance")
        if balance is not None:
            # Format with two decimal places and thousands separator
            display_balance = float(balance) / 100
            formatted_balance = "{:,.2f}".format(display_balance).replace(",", " ")
            balance_text = _("\n💰 <b>Balance:</b> {balance} UZS").format(
                balance=formatted_balance
            )

    await callback.message.edit_text(
        _(
            "🏠 <b>Account: {username}</b>{balance}\n\n"
            "Please select a time period below to analyze your electricity consumption:"
        ).format(username=username, balance=balance_text),
        reply_markup=get_period_keyboard(account_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_PERIOD))
async def view_period_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Fetch and display consumption data for selected period.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    # Parse callback data: period:account_id:period_type
    try:
        parts = callback.data.split(":")
        account_id = UUID(parts[1])
        period = parts[2]
    except (IndexError, ValueError):
        await callback.answer(str(_("❌ Invalid request")), show_alert=True)
        return

    # If yearly, show year selection first
    if period == "yearly":
        await callback.message.edit_text(
            _("📊 <b>Yearly Consumption</b>\n\nPlease select a year to view:"),
            reply_markup=get_year_selection_keyboard(account_id),
        )
        await callback.answer()
        return

    # Show loading message
    await callback.answer(_("⏳ Fetching your data... Please wait."))

    try:
        # Get account and access token
        telegram_user = await TelegramUserService.get_user(
            session, chat_id=str(callback.from_user.id)
        )

        account_link = None
        for link in telegram_user.users:
            if link.user.id == account_id:
                account_link = link
                break

        if not account_link:
            await callback.message.answer(
                _("⚠️ <b>Account Not Found</b>\n\nCould not locate the specified account.")
            )
            return

        access_token = account_link.access_token

        # Process data and generate chart
        chart_data, title = await process_chart_data(
            callback.bot.session_client, period, access_token, _
        )

        # Generate chart image
        image_buffer = await ChartService.generate_consumption_chart(
            chart_data,
            period,
            title,
            x_label=_("Period"),
            y_label=_("Consumption (kWh)"),
        )

        # Send photo
        username = account_link.user.username
        caption = _("📊 <b>{title}</b>\n\n" "👤 <b>Account:</b> {username}").format(
            title=title, username=username
        )

        if callback.message.photo:
            await callback.message.delete()

        await callback.message.answer_photo(
            photo=BufferedInputFile(image_buffer.read(), filename="chart.png"),
            caption=caption,
            reply_markup=get_stats_keyboard(account_id, period),
        )

    except Exception as e:
        await callback.message.answer(
            str(_("❌ An error occurred while fetching data: {error}")).format(
                error=str(e)
            )
        )


@router.callback_query(F.data.startswith(CB_SELECT_YEAR))
async def select_year_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Handle year selection for yearly consumption chart.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    # Parse callback data: select_year:account_id:year
    try:
        parts = callback.data.split(":")
        account_id = UUID(parts[1])
        year = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer(str(_("❌ Invalid request")), show_alert=True)
        return

    # Show loading message
    await callback.answer(_("⏳ Fetching {year} data...").format(year=year))

    try:
        # Get account and access token
        telegram_user = await TelegramUserService.get_user(
            session, chat_id=str(callback.from_user.id)
        )

        account_link = _get_account_link(telegram_user, account_id)

        if not account_link:
            await callback.message.answer(
                _("⚠️ <b>Account Not Found</b>\n\nCould not locate the specified account.")
            )
            return

        access_token = account_link.access_token

        # Process data for selected year
        labels, values = await _process_yearly_data(
            callback.bot.session_client, access_token, year
        )
        chart_data = {"labels": labels, "values": values}
        title = f"{year} Consumption"

        # Generate chart image
        image_buffer = await ChartService.generate_consumption_chart(
            chart_data,
            "yearly",
            title,
            x_label=_("Month"),
            y_label=_("Consumption (kWh)"),
        )

        # Send photo
        username = account_link.user.username
        caption = _("📊 <b>{title}</b>\n\n👤 <b>Account:</b> {username}").format(
            title=title, username=username
        )

        if callback.message.photo:
            await callback.message.delete()

        await callback.message.answer_photo(
            photo=BufferedInputFile(image_buffer.read(), filename="chart.png"),
            caption=caption,
            reply_markup=get_stats_keyboard(account_id, "yearly"),
        )

    except Exception as e:
        await callback.message.answer(
            str(_("❌ An error occurred while fetching data: {error}")).format(
                error=str(e)
            )
        )


@router.callback_query(F.data.startswith(CB_SWITCH_PERIOD))
async def switch_period_callback(callback: CallbackQuery, _):
    """
    Show period selection keyboard again.

    Args:
        callback: Callback query
        _: Translation function
    """
    try:
        account_id = UUID(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(_("❌ Invalid account"), show_alert=True)
        return

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            _("📅 Select a period:"), reply_markup=get_period_keyboard(account_id)
        )
    else:
        await callback.message.edit_text(
            _("📅 Select a period:"), reply_markup=get_period_keyboard(account_id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_PAYMENTS))
async def show_payments_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Show payment history for the account.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    try:
        account_id = UUID(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(_("❌ Invalid account"), show_alert=True)
        return

    await callback.answer(_("⏳ Fetching payments..."))

    try:
        # Get account access token
        telegram_user = await TelegramUserService.get_user(
            session, chat_id=str(callback.from_user.id)
        )

        account_link = None
        for link in telegram_user.users:
            if link.user.id == account_id:
                account_link = link
                break

        if not account_link:
            await callback.message.answer(
                _("⚠️ <b>Account Not Found</b>\n\nPlease try again.")
            )
            return

        access_token = account_link.access_token

        # Fetch payments
        data, status = await het_service.get_payments(
            callback.bot.session_client, access_token, page=0, size=10
        )

        if status != 200:
            await callback.message.answer(
                _("⚠️ <b>Connection Error</b>\n\nFailed to retrieve payment history.")
            )
            return

        # Format payment history
        payments_text = _format_payments_history(data, _)

        if callback.message.photo:
            await callback.message.delete()

        await callback.message.answer(
            payments_text, reply_markup=get_stats_keyboard(account_id, "payments")
        )

    except Exception as e:
        await callback.message.answer(
            _("❌ Error fetching payments: {error}").format(error=str(e))
        )


@router.callback_query(F.data.startswith(CB_READINGS))
async def show_readings_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Fetch and display meter reading history.
    """
    try:
        data_parts = callback.data.split(":")
        if len(data_parts) < 2:
            return
        account_id = UUID(data_parts[1])

        # Fetch user and session implicitly through data middleware
        telegram_user = await TelegramUserService.get_user(
            session, chat_id=str(callback.from_user.id)
        )

        account_link = _get_account_link(telegram_user, account_id)
        if not account_link:
            await callback.message.answer(_("❌ Invalid account"))
            return

        access_token = account_link.access_token
        data, status = await het_service.get_reading_histories(
            callback.bot.session_client, access_token
        )

        if status != 200:
            await callback.message.answer(
                _("⚠️ <b>Connection Error</b>\n\nFailed to retrieve reading history.")
            )
            return

        readings_text = _("📟 <b>Meter Readings</b>\n\n")
        items = data.get("content", [])

        if not items:
            readings_text += _("<i>No reading records found.</i>")
        else:
            for item in items:
                date = item.get("readingDate", "Unknown")
                value = item.get("readingAPlus", 0)
                status_name = item.get("meterReadingStatus", {}).get("name", "OK")
                source = item.get("readingSourceType", "API")
                readings_text += (
                    f"📅 <b>{date}</b>\n"
                    f"🔢 {value} kWh\n"
                    f"✅ {status_name} ({source})\n"
                    "-------------------\n"
                )

        if callback.message.photo:
            await callback.message.delete()

        await callback.message.answer(
            readings_text, reply_markup=get_stats_keyboard(account_id, "readings")
        )
        await callback.answer()

    except Exception as e:
        await callback.message.answer(
            _("❌ Error fetching readings: {error}").format(error=str(e))
        )


@router.callback_query(F.data.startswith(CB_DELETE))
async def delete_account_callback(callback: CallbackQuery, _):
    """
    Show confirmation dialog for account deletion.

    Args:
        callback: Callback query
        _: Translation function
    """
    try:
        account_id = UUID(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(_("❌ Invalid account"), show_alert=True)
        return

    text = _(
        "🗑 <b>Delete Account?</b>\n\n"
        "Are you sure you want to remove this account?\n"
        "<i>This action will unlink it from the bot, but you can always add it back later.</i>"
    )
    reply_markup = get_confirm_keyboard("delete", account_id)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup)
    else:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data.startswith(CB_CONFIRM_DELETE))
async def confirm_delete_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Delete account after confirmation.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    try:
        account_id = UUID(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(_("❌ Invalid account"), show_alert=True)
        return

    try:
        await TelegramUserService.remove_user(
            session, chat_id=str(callback.from_user.id), user_id=account_id
        )

        text = _(
            "✅ <b>Account Removed</b>\n\nThe account has been successfully unlinked."
        )
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text)
        else:
            await callback.message.edit_text(text)
        await callback.answer()

        # Show main menu
        await callback.message.answer(
            _("Use the menu to manage your remaining accounts:"),
            reply_markup=get_main_menu_keyboard(),
        )

    except Exception as e:
        await callback.message.answer(
            _("❌ Error deleting account: {error}").format(error=str(e))
        )
        await callback.answer()


@router.callback_query(F.data == CB_CANCEL)
async def cancel_callback(callback: CallbackQuery, _):
    """
    Cancel current operation and return to main view.

    Args:
        callback: Callback query
        _: Translation function
    """
    text = _("🚫 <b>Action Cancelled</b>")
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text)
    else:
        await callback.message.edit_text(text)
    await callback.answer()

    await callback.message.answer(
        _("What would you like to do next?"), reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == CB_BACK)
async def back_callback(callback: CallbackQuery, session: AsyncSession, _):
    """
    Navigate back to accounts list.

    Args:
        callback: Callback query
        session: Database session
        _: Translation function
    """
    telegram_user = await TelegramUserService.get_user(
        session, chat_id=str(callback.from_user.id)
    )

    if not telegram_user or not telegram_user.users:
        await callback.message.edit_text(_("You don't have any accounts."))
        await callback.answer()
        return

    accounts = [
        {"id": str(link.user.id), "username": link.user.username}
        for link in telegram_user.users
    ]

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            _(
                "📋 <b>Your HET Accounts</b>\n\nSelect an account below to view detailed statistics and consumption data:"
            ),
            reply_markup=get_accounts_keyboard(accounts),
        )
    else:
        await callback.message.edit_text(
            _(
                "📋 <b>Your HET Accounts</b>\n\nSelect an account below to view detailed statistics and consumption data:"
            ),
            reply_markup=get_accounts_keyboard(accounts),
        )
    await callback.answer()
