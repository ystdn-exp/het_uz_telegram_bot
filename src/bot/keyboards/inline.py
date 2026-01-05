"""
Inline keyboard builders for the bot.
"""

from typing import List
from uuid import UUID

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.constants import (
    BTN_TODAY,
    BTN_WEEKLY,
    BTN_MONTHLY,
    BTN_YEARLY,
    BTN_SWITCH_PERIOD,
    BTN_PAYMENTS,
    BTN_READINGS,
    BTN_BACK,
    BTN_DELETE,
    BTN_CONFIRM,
    BTN_CANCEL,
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


def get_accounts_keyboard(accounts: List[dict]) -> InlineKeyboardMarkup:
    """
    Build inline keyboard with list of user's HET accounts.

    Args:
        accounts: List of account dictionaries with 'id' and 'username' keys

    Returns:
        InlineKeyboardMarkup: Accounts list keyboard
    """
    builder = InlineKeyboardBuilder()

    for account in accounts:
        account_id = account.get("id")
        username = account.get("username", "Unknown")
        builder.button(
            text=f"🏠 {username}",
            callback_data=f"{CB_VIEW_ACCOUNT}:{account_id}"
        )

    # One button per row
    builder.adjust(1)

    return builder.as_markup()


def get_period_keyboard(account_id: UUID) -> InlineKeyboardMarkup:
    """
    Build period selection keyboard for viewing statistics.

    Args:
        account_id: The HET account ID

    Returns:
        InlineKeyboardMarkup: Period selection keyboard
    """
    builder = InlineKeyboardBuilder()

    periods = [
        (BTN_TODAY, "today"),
        (BTN_WEEKLY, "weekly"),
        (BTN_MONTHLY, "monthly"),
        (BTN_YEARLY, "yearly"),
    ]

    for btn_text, period in periods:
        builder.button(
            text=str(btn_text),
            callback_data=f"{CB_PERIOD}:{account_id}:{period}"
        )

    # Add back button
    builder.button(
        text=str(BTN_BACK),
        callback_data=CB_BACK
    )

    # 2 buttons per row, except last row with back button
    builder.adjust(2, 2, 1)

    return builder.as_markup()


def get_stats_keyboard(
    account_id: UUID, current_period: str
) -> InlineKeyboardMarkup:
    """
    Build statistics view keyboard with actions.

    Args:
        account_id: The HET account ID
        current_period: Current period being viewed

    Returns:
        InlineKeyboardMarkup: Stats keyboard with actions
    """
    builder = InlineKeyboardBuilder()

    # Switch Period button
    builder.button(
        text=str(BTN_SWITCH_PERIOD),
        callback_data=f"{CB_SWITCH_PERIOD}:{account_id}"
    )

    # Payments button
    builder.button(
        text=str(BTN_PAYMENTS),
        callback_data=f"{CB_PAYMENTS}:{account_id}"
    )

    # Meter Readings button
    builder.button(
        text=str(BTN_READINGS),
        callback_data=f"{CB_READINGS}:{account_id}"
    )

    # Delete Account button
    builder.button(
        text=str(BTN_DELETE),
        callback_data=f"{CB_DELETE}:{account_id}"
    )

    # Back button
    builder.button(
        text=str(BTN_BACK),
        callback_data=CB_BACK
    )

    # 2 buttons per row
    builder.adjust(2, 2, 1)

    return builder.as_markup()


def get_confirm_keyboard(action: str, account_id: UUID) -> InlineKeyboardMarkup:
    """
    Build confirmation keyboard for destructive actions.

    Args:
        action: The action to confirm (e.g., "delete")
        account_id: The HET account ID

    Returns:
        InlineKeyboardMarkup: Confirmation keyboard
    """
    builder = InlineKeyboardBuilder()

    # Confirm button
    builder.button(
        text=str(BTN_CONFIRM),
        callback_data=f"{CB_CONFIRM_DELETE}:{account_id}"
    )

    # Cancel button
    builder.button(
        text=str(BTN_CANCEL),
        callback_data=CB_CANCEL
    )

    # 2 buttons per row
    builder.adjust(2)

    return builder.as_markup()


def get_year_selection_keyboard(account_id: UUID) -> InlineKeyboardMarkup:
    """
    Build year selection keyboard for yearly consumption chart.

    Args:
        account_id: The HET account ID

    Returns:
        InlineKeyboardMarkup: Year selection keyboard
    """
    from datetime import datetime

    builder = InlineKeyboardBuilder()

    # Offer last 3 years (current + 2 previous)
    current_year = datetime.now().year
    years = [current_year - 2, current_year - 1, current_year]

    for year in years:
        builder.button(
            text=f"📅 {year}",
            callback_data=f"{CB_SELECT_YEAR}:{account_id}:{year}"
        )

    # Add back button
    builder.button(
        text=str(BTN_BACK),
        callback_data=f"{CB_SWITCH_PERIOD}:{account_id}"
    )

    # 3 years per row, then back button
    builder.adjust(3, 1)

    return builder.as_markup()
