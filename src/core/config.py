import os

from typing import Annotated, Any
from pathlib import Path

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(value: Any) -> list[str] | str:
    """
    Helper function to validate CORS configuration.

    validation steps:
    1. validate string values -> e.g. localhost,127.0.0.1
    2. if it is already list or string return it
    3. raise ValueError on other types
    """
    if isinstance(value, str) and not value.startswith("["):
        return [character.strip() for character in value.split(",")]
    elif isinstance(value, list | str):
        return value

    return ValueError(value)


class Settings(BaseSettings):
    """
    A class to store .env variables.
    """

    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    BASE_DIR: Path = Path(__name__).resolve().parent.parent.parent

    PROJECT_NAME: str = "HET"
    SECRET_KEY: str
    DEBUG: bool

    SECRET_KEY: str
    TELEGRAM_SECRET_KEY: str

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field
    @property
    def ALL_CORS_ORIGINS(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    SENTRY_DSN: HttpUrl | None = None

    SQL_HOST: str
    SQL_PORT: int
    SQL_USER: str
    SQL_PASSWORD: str
    SQL_DB: str

    # database configuration with caching method
    @computed_field
    @property
    def AI_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.SQL_AI_USER,
            password=self.SQL_AI_PASSWORD,
            host=self.SQL_AI_HOST,
            port=self.SQL_AI_PORT,
            path=self.SQL_AI_DB,
        )

    # redis configuration
    REDIS_HOST: str
    REDIS_PORT: int

    # logging parameters
    LOG_DIR: Path = os.path.join(BASE_DIR, "logs")
    LOG_LEVEL: str = "INFO"
    ROTATING_LOG_FILE_SIZE: int = 10 * 1024 * 1024
    ROTATING_LOG_FILE_BACKUPS: int = 5


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
