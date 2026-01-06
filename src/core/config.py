import ipaddress
import os
from pathlib import Path
from typing import Annotated, Any, List, Optional, Union

from pydantic import AnyUrl, BeforeValidator, HttpUrl, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(value: Any) -> Union[List[str], str]:
    """
    Helper function to validate CORS configuration.

    validation steps:
    1. validate string values -> e.g. localhost,127.0.0.1
    2. if it is already list or string return it
    3. raise ValueError on other types
    """
    if isinstance(value, str) and not value.startswith("["):
        return [character.strip() for character in value.split(",")]
    elif isinstance(value, (list, str)):
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

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    BASE_URL: Optional[str] = None
    # NGROK_URL: Optional[str] = None  # only for development
    ENVIRONMENT: str = None  # development | production

    PROJECT_NAME: str = "HET"
    SECRET_KEY: str
    DEBUG: bool

    TIMEZONE: str = "UTC"

    SECRET_KEY: str
    WEBHOOK_SECRET_KEY: str

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str

    BACKEND_CORS_ORIGINS: Annotated[
        Union[List[AnyUrl], str], BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def ALL_CORS_ORIGINS(self) -> List[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    SENTRY_DSN: Union[HttpUrl, None] = None

    SQL_HOST: str
    SQL_PORT: int
    SQL_USER: str
    SQL_PASSWORD: str
    SQL_DB: str

    # redis configuration
    REDIS_HOST: str
    REDIS_PORT: int

    # logging parameters
    LOG_DIR: Path = os.path.join(BASE_DIR, "logs")
    LOG_LEVEL: str = "INFO"
    ROTATING_LOG_FILE_SIZE: int = 10 * 1024 * 1024
    ROTATING_LOG_FILE_BACKUPS: int = 5

    # webhook
    TELEGRAM_WHITELIST_IPS: List = [
        "149.154.160.0/20",
        "91.108.4.0/22",
    ]  # telegram's default ip address

    # dynamically get webhook url regarding to the environment
    # @property
    # def WEBHOOK_URL(self) -> str:
    #     base_host = ""

    #     if self.ENVIRONMENT == "development":
    #         base_host = self.NGROK_URL
    #     elif self.ENVIRONMENT == "production":
    #         base_host = self.BASE_URL

    #     return f"{base_host}/bot/webhook"

    # database configuration with caching method
    @computed_field
    @property
    def SQL_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.SQL_USER,
            password=self.SQL_PASSWORD,
            host=self.SQL_HOST,
            port=self.SQL_PORT,
            path=self.SQL_DB,
        )

    @computed_field
    @property
    def TELEGRAM_IP_RANGES(
        self,
    ) -> List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
        return [
            ipaddress.ip_network(ip_whitelist)
            for ip_whitelist in self.TELEGRAM_WHITELIST_IPS
        ]


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
