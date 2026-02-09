import contextvars
import os
from typing import Any

from babel.support import Translations

from src.core.config import settings

current_locale = contextvars.ContextVar("current_locale", default="en")


def get_locale() -> str:
    return current_locale.get()


def set_locale(locale: str) -> str:
    current_locale.set(locale)


class TranslationManager:
    """A manager class to perform cache based gettext operations."""

    def __init__(self):
        self._cache: dict[str, Translations] = {}
        self.locales_path = os.path.join(settings.BASE_DIR, "locales")
        self.default_locale = "en"
        # List of supported locales (those with translation files)
        self.supported_locales = ["en", "ru", "uz"]

    def get_translations(self, locale: str) -> Translations:
        # Use default locale if requested locale is not supported
        active_locale = (
            locale if locale in self.supported_locales else self.default_locale
        )

        if active_locale not in self._cache:
            self._cache[active_locale] = Translations.load(
                self.locales_path, [active_locale], domain="messages"
            )

        return self._cache[active_locale]


i18n = TranslationManager()


class lazy_gettext(str):
    """A lazy gettext class that works on module level."""

    def __new__(cls, key: str):
        return super().__new__(cls, key)

    def __init__(self, key: str):
        self.__key = key

    def __getattr__(self, name: str) -> Any:
        # if any method is called on the lazy_gettext object,
        # we need to translate first then call the method on real string
        return getattr(str(self), name)

    def __str__(self) -> str:
        locale = get_locale()
        translations = i18n.get_translations(locale)
        _ = translations.gettext
        return _(self.__key)

    def __bool__(self):
        return bool(self.__key)

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __format__(self, format_spec: str) -> str:
        return format(str(self), format_spec)

    def __add__(self, other: Any) -> str:
        return str(self) + str(other)

    def __radd__(self, other: Any) -> str:
        return str(other) + str(self)

    def __contains__(self, item: str) -> bool:
        return item in str(self)

    def __iter__(self):
        return iter(str(self))

    def __getitem__(self, index: Any) -> str:
        return str(self)[index]

    def __mod__(self, other: Any) -> str:
        return str(self) % other

    def __rmod__(self, other: Any) -> str:
        return str(other) % str(self)

    def __mul__(self, other: int) -> str:
        return str(self) * other

    def __rmul__(self, other: int) -> str:
        return other * str(self)

    def __lt__(self, other: Any) -> bool:
        return str(self) < str(other)

    def __le__(self, other: Any) -> bool:
        return str(self) <= str(other)

    def __gt__(self, other: Any) -> bool:
        return str(self) > str(other)

    def __ge__(self, other: Any) -> bool:
        return str(self) >= str(other)

    def lower(self) -> str:
        return str(self).lower()

    def upper(self) -> str:
        return str(self).upper()

    def strip(self, chars: str = None) -> str:
        return str(self).strip(chars)

    def lstrip(self, chars: str = None) -> str:
        return str(self).lstrip(chars)

    def rstrip(self, chars: str = None) -> str:
        return str(self).rstrip(chars)

    def startswith(self, prefix: str, start: int = 0, end: int = None) -> bool:
        return str(self).startswith(prefix, start, end)

    def endswith(self, suffix: str, start: int = 0, end: int = None) -> bool:
        return str(self).endswith(suffix, start, end)

    def replace(self, old: str, new: str, count: int = -1) -> str:
        return str(self).replace(old, new, count)

    def split(self, sep: str = None, maxsplit: int = -1) -> list[str]:
        return str(self).split(sep, maxsplit)

    def rsplit(self, sep: str = None, maxsplit: int = -1) -> list[str]:
        return str(self).rsplit(sep, maxsplit)

    def join(self, iterable: Any) -> str:
        return str(self).join(iterable)

    def find(self, sub: str, start: int = 0, end: int = None) -> int:
        return str(self).find(sub, start, end)

    def rfind(self, sub: str, start: int = 0, end: int = None) -> int:
        return str(self).rfind(sub, start, end)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        """Make lazy_gettext compatible with Pydantic v2."""
        from pydantic_core import core_schema

        return core_schema.no_info_before_validator_function(
            lambda x: str(x),
            core_schema.str_schema(),
        )


# business rules
# - we use _() for inner logic (handlers in aiogram) via setting in middleware: data["_"] = i18n.get_translations(language).gettext
# - we use l_() for module level operations (constants, etc.) via lazy_gettext object
