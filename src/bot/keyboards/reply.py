"""
Reply keyboard builders for the bot.
"""

from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.bot.keyboards.constants import (
    BTN_ADD_ACCOUNT,
    BTN_MY_ACCOUNTS,
    BTN_HELP,
    BTN_CHANGE_LANGUAGE,
    BTN_LANG_EN,
    BTN_LANG_RU,
    BTN_LANG_UZ,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Build the main menu reply keyboard.

    Returns:
        ReplyKeyboardMarkup: Main menu keyboard
    """
    builder = ReplyKeyboardBuilder()

    # Row 1: Add Account, My Accounts
    builder.button(text=str(BTN_ADD_ACCOUNT))
    builder.button(text=str(BTN_MY_ACCOUNTS))

    # Row 2: Help, Change Language
    builder.button(text=str(BTN_HELP))
    builder.button(text=str(BTN_CHANGE_LANGUAGE))

    # Adjust layout: 2 buttons in each row
    builder.adjust(2, 2)

    return builder.as_markup(resize_keyboard=True)


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """
    Remove the keyboard.

    Returns:
        ReplyKeyboardRemove: Keyboard removal object
    """
    return ReplyKeyboardRemove()


def get_language_keyboard() -> ReplyKeyboardMarkup:
    """
    Build the language selection keyboard.

    Returns:
        ReplyKeyboardMarkup: Language selection keyboard
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text=BTN_LANG_EN)
    builder.button(text=BTN_LANG_RU)
    builder.button(text=BTN_LANG_UZ)

    builder.adjust(1)  # one button per row

    return builder.as_markup(resize_keyboard=True)
