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

    RESTAURANT_SECRET_KEY: str

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field
    @property
    def ALL_CORS_ORIGINS(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    SENTRY_DSN: HttpUrl | None = None

    # JOWi AI database
    SQL_AI_HOST: str
    SQL_AI_PORT: int
    SQL_AI_USER: str
    SQL_AI_PASSWORD: str
    SQL_AI_DB: str

    # restaurant database
    SQL_WEB_HOST: str
    SQL_WEB_PORT: int
    SQL_WEB_USER: str
    SQL_WEB_PASSWORD: str
    SQL_WEB_DB: str

    # super admin database
    SQL_SUPER_ADMIN_HOST: str
    SQL_SUPER_ADMIN_PORT: int
    SQL_SUPER_ADMIN_USER: str
    SQL_SUPER_ADMIN_PASSWORD: str
    SQL_SUPER_ADMIN_DB: str

    RESTAURANT_ACCESS_TOKEN_EXPIRE_DAYS: int = 1
    SUPER_ADMIN_ACCESS_TOKEN_EXPIRE_DAYS: int = 1
    ALGORITHM: str = "HS256"

    # JOWi AI database
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

    # restaurant database
    @computed_field
    @property
    def WEB_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.SQL_WEB_USER,
            password=self.SQL_WEB_PASSWORD,
            host=self.SQL_WEB_HOST,
            port=self.SQL_WEB_PORT,
            path=self.SQL_WEB_DB,
        )

    # super admin database
    @computed_field
    @property
    def SUPER_ADMIN_DATABASE_URI(self) -> PostgresDsn:
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


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
