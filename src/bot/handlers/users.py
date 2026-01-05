"""
User account management handlers and callbacks.
"""

from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.users import TelegramUserService
from src.services.het import het_service
from src.services.charts import ChartService
from src.bot.keyboards.inline import (
    get_accounts_keyboard,
    get_period_keyboard,
    get_stats_keyboard,
    get_confirm_keyboard,
    get_year_selection_keyboard,
)
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.bot.keyboards.constants import (
    BTN_MY_ACCOUNTS,
    BTN_HELP,
    CB_VIEW_ACCOUNT,
    CB_PERIOD,
    CB_SWITCH_PERIOD,
    CB_PAYMENTS,
    CB_READINGS,
    CB_DELETE,
    CB_CONFIRM_DELETE,
    CB_CANCEL,
    CB_BACK,
    CB_SELECT_YEAR,
)

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
    data, status = await het_service.get_consumer_state(access_token)

    # Handle expired token
    if status == 401 and account_link.refresh_token:
        new_tokens, refresh_status = await het_service.refresh_token(
            account_link.refresh_token
        )
        if refresh_status == 200 and new_tokens.get("data"):
            tokens = new_tokens["data"]
            account_link.access_token = tokens.get("accessToken")
            account_link.refresh_token = tokens.get("refreshToken")
            session.add(account_link)
            await session.commit()
            access_token = account_link.access_token
            # Retry fetch
            data, status = await het_service.get_consumer_state(access_token)

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


def _get_account_link(telegram_user, account_id: UUID):
    """Helper to find account link for a user."""
    for link in telegram_user.users:
        if link.user.id == account_id:
            return link
    return None


async def _process_yearly_data(access_token: str, year: int):
    """Fetch and process yearly consumption data (monthly aggregates)."""
    labels, values = [], []
    data, status = await het_service.get_monthly_consumption(access_token, year)

    if status == 200:
        raw_data = data.get("data")
        items = raw_data if isinstance(raw_data, list) else []

        # Aggregate values by month
        aggregated = {}
        for item in items:
            raw_label = item.get("period") or item.get("month") or item.get("date")
            label = _format_yearly_label(raw_label)
            if label:
                value = (
                    item.get("totalCalcKwh")
                    or item.get("consumption")
                    or item.get("calculateKwh")
                    or 0
                )
                # Convert Wh to kWh by dividing by 1000
                aggregated[label] = aggregated.get(label, 0) + (float(value) / 1000)

        # Define month order for sorting
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_order = {m: i for i, m in enumerate(months)}

        # Sort by month order
        sorted_keys = sorted(aggregated.keys(), key=lambda x: month_order.get(x, 99))
        for k in sorted_keys:
            labels.append(k)
            values.append(aggregated[k])

    return labels, values


def _format_yearly_label(raw_label: Any) -> Optional[str]:
    """Format yearly/monthly data labels into readable month names."""
    if not raw_label:
        return None

    str_label = str(raw_label)
    if "-" in str_label:
        try:
            dt = datetime.strptime(str_label.split(" ")[0], "%Y-%m-%d")
            return dt.strftime("%b")
        except Exception:
            return str_label
    elif str_label.isdigit():
        try:
            month_idx = int(str_label)
            return datetime(2000, month_idx, 1).strftime("%b")
        except Exception:
            return str_label
    return str_label


async def _process_reading_based_data(access_token: str, period: str):
    """Fetch and process daily/weekly/monthly consumption data from readings."""
    labels, values = [], []
    # Fetch enough records for the period (Today: 2, Weekly: 8, Monthly: 32)
    size = 2 if period == "today" else (8 if period == "weekly" else 35)
    data, status = await het_service.get_reading_histories(access_token, size=size)

    if status == 200:
        # Based on HET API structure: {"content": [...]}
        items = data.get("content", [])
        if len(items) >= 2:
            for i in range(len(items) - 1):
                label, consumption = _calculate_consumption(items[i], items[i + 1])
                if label and consumption is not None:
                    labels.append(label)
                    values.append(consumption)

            limit = 1 if period == "today" else (7 if period == "weekly" else 30)
            labels = labels[:limit]
            values = values[:limit]
            labels.reverse()
            values.reverse()

    return labels, values


def _calculate_consumption(current_item: dict, prev_item: dict) -> tuple[str, float]:
    """Calculate consumption between two readings and format label."""
    try:
        current_val = current_item.get("readingAPlus")
        prev_val = prev_item.get("readingAPlus")
        date_str = current_item.get("readingDate")

        if current_val is None or prev_val is None:
            return None, None

        consumption = float(current_val) - float(prev_val)
        if consumption < 0:
            consumption = 0

        if date_str:
            try:
                dt = datetime.strptime(str(date_str).split(" ")[0], "%Y-%m-%d")
                label = dt.strftime("%d.%m")
            except Exception:
                label = str(date_str)
        else:
            label = "???"

        return label, consumption
    except (ValueError, TypeError):
        return None, None


async def process_chart_data(period: str, access_token: str, _) -> tuple[dict, str]:
    """
    Helper to fetch and format data for charts based on HET API response.
    """
    title = ""

    if period == "today":
        title = _("Today Consumption")
    elif period == "weekly":
        title = _("Weekly Consumption")
    elif period == "monthly":
        title = _("Monthly Consumption")

    if period == "yearly":
        # Fallback - main flow uses select_year_callback
        labels, values = await _process_yearly_data(access_token, datetime.now().year)
    elif period in ["today", "weekly", "monthly"]:
        labels, values = await _process_reading_based_data(access_token, period)
    else:
        labels, values = [], []

    # Fallback if no data found
    if not labels:
        data, status = await het_service.get_consumer_state(access_token)
        if status == 200:
            raw_data = data.get("data", {})
            usage = raw_data.get("currentMonthCalcKwh") or raw_data.get("usage")
            if usage is not None:
                labels = ["Current Mo"]
                values = [float(usage)]

    return {"labels": labels, "values": values}, title


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
            reply_markup=get_year_selection_keyboard(account_id)
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
                _(
                    "⚠️ <b>Account Not Found</b>\n\nCould not locate the specified account."
                )
            )
            return

        access_token = account_link.access_token

        # Process data and generate chart
        chart_data, title = await process_chart_data(period, access_token, _)

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
                _(
                    "⚠️ <b>Account Not Found</b>\n\nCould not locate the specified account."
                )
            )
            return

        access_token = account_link.access_token

        # Process data for selected year
        labels, values = await _process_yearly_data(access_token, year)
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
        data, status = await het_service.get_payments(access_token, page=0, size=10)

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
        data, status = await het_service.get_reading_histories(access_token)

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

        text = _("✅ <b>Account Removed</b>\n\nThe account has been successfully unlinked.")
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


def _format_payments_history(data: dict, _) -> str:
    """Helper to format payment history text."""
    payments_text = _("💳 <b>Payment History</b>\n\n")
    payments = data.get("content", [])

    if not payments:
        payments_text += _("<i>No payment records found for this account.</i>")
    else:
        for payment in payments:
            date = payment.get("paymentDate", "N/A")
            amount = payment.get("paymentAmount", 0)
            pay_type = payment.get("paymentType", {}).get("name") or "Unknown"
            purpose = payment.get("householdPaymentPurpose", {}).get("name") or _(
                "Electricity"
            )

            # Format with two decimal places and thousands separator
            display_amount = float(amount) / 100
            formatted_amount = "{:,.2f}".format(display_amount).replace(",", " ")

            payments_text += (
                f"📅 <b>{date}</b>\n"
                f"💰 {formatted_amount} UZS\n"
                f"🔌 {purpose} ({pay_type})\n"
                "-------------------\n"
            )
    return payments_text
