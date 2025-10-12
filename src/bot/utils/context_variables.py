import os
import contextvars

from typing import Optional

from src.core.config import settings
from babel.support import Translations


current_locale = contextvars.ContextVar("current_locale", default="en")


def get_locale() -> str:
    return current_locale.get()


def set_locale(locale: str) -> str:
    current_locale.set(locale)


def get_translations(locale: Optional[str] = None) -> Translations:
    locale = locale or get_locale()
    path = os.path.join(settings.BASE_DIR, "locales")
    return Translations.load(path, [locale], domain="messages")


_ = lambda s: get_translations().gettext(s)
ngettext = lambda s1, s2, n: get_translations().ngettext(s1, s2, n)
