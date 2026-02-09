"""
Keyboard constants with i18n support.
"""

from src.bot.utils.context_variables import lazy_gettext as l_

# Main menu buttons
BTN_ADD_ACCOUNT = l_("➕ Add Account")
BTN_MY_ACCOUNTS = l_("👁 My Accounts")
BTN_HELP = l_("ℹ️ Help")
BTN_CHANGE_LANGUAGE = l_("🌐 Change Language")

# Language buttons
BTN_LANG_EN = "🇺🇸 English"
BTN_LANG_RU = "🇷🇺 Русский"
BTN_LANG_UZ = "🇺🇿 O'zbek"

# Period selection buttons
BTN_TODAY = l_("📅 Today")
BTN_WEEKLY = l_("📈 Weekly")
BTN_MONTHLY = l_("📆 Monthly")
BTN_YEARLY = l_("📊 Yearly")

# Action buttons
BTN_SWITCH_PERIOD = l_("📊 Consumption")
BTN_PAYMENTS = l_("💳 Payments")
BTN_READINGS = l_("📟 Meter Readings")
BTN_BACK = l_("🔙 Back")
BTN_DELETE = l_("🗑 Delete")
BTN_CANCEL = l_("❌ Cancel")
BTN_CONFIRM = l_("✅ Confirm")

# Callback data prefixes
CB_VIEW_ACCOUNT = "view_account"
CB_PERIOD = "period"
CB_SWITCH_PERIOD = "switch_period"
CB_PAYMENTS = "payments"
CB_READINGS = "readings"
CB_DELETE = "delete"
CB_CONFIRM_DELETE = "confirm_delete"
CB_CANCEL = "cancel"
CB_BACK = "back"
CB_SELECT_YEAR = "select_year"
