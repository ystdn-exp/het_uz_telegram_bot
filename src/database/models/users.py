from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import BaseModel

# business rules:
# - one telegram user can only have up to 3 accounts


class User(BaseModel):
    """User model for HET system."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(512))

    telegram_users: Mapped[list["UserInTelegramUser"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class TelegramUser(BaseModel):
    """User model for telegram."""

    __tablename__ = "telegram_users"

    username: Mapped[str] = mapped_column(String(32))
    chat_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    users: Mapped[list["UserInTelegramUser"]] = relationship(
        back_populates="telegram_user", cascade="all, delete-orphan"
    )


class UserInTelegramUser(BaseModel):
    """Many to many relationship between User and TelegramUser."""

    __tablename__ = "user_in_telegram_user"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    telegram_user_id: Mapped[UUID] = mapped_column(ForeignKey("telegram_users.id"))

    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)

    access_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=True
    )  # access token expires in 6 hours (21600 seconds), we should use refresh token
    # if refresh token updated time is expired (more than 40 days) we login using existing creds

    user: Mapped["User"] = relationship(back_populates="telegram_users")
    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="users")
