"""
Database services for users.
"""

from uuid import UUID

import httpx
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.bot.exceptions import ValidationError
from src.bot.utils import lazy_gettext as l_
from src.core.security import password_encoder
from src.database.models import TelegramUser, User, UserInTelegramUser
from src.services.het import het_service


class UserService:
    """
    UserService class for handling database operations related to users.
    """

    @classmethod
    async def get_user(cls, session: AsyncSession, **fields) -> User:
        """
        Get a user by fields.

        Args:
            session (AsyncSession): The database session.

        Returns:
            User: The user object.
        """
        where_clause = [getattr(User, key) == value for key, value in fields.items()]

        query = select(User).where(*where_clause)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def verify_het_account(
        cls, client: httpx.AsyncClient, username: str, password: str
    ):
        """
        Verify het account using HET service.
        """
        try:
            response, status = await het_service.authorize(client, username, password)

            if status != 200:
                raise ValidationError(l_("Invalid username or password"))

            access_token = response.get("data").get("accessToken")
            refresh_token = response.get("data").get("refreshToken")

            return access_token, refresh_token
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValidationError(l_("Invalid username or password"))
            elif e.response.status_code == 400:
                try:
                    error_msg = e.response.json().get("message", "Invalid input")
                    raise ValidationError(error_msg)
                except Exception:
                    raise ValidationError(l_("Invalid input data"))
            raise ValidationError(l_("HET API error. Please try again later."))
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError(l_("HET service is temporarily unavailable."))

    @classmethod
    async def update_user_tokens(
        cls, session: AsyncSession, user_id: UUID, access_token: str, refresh_token: str
    ):
        """
        Update user tokens in the UserInTelegramUser link table.

        Args:
            session (AsyncSession): Database session
            user_id (UUID): User ID
            access_token (str): New access token
            refresh_token (str): New refresh token
        """
        await TelegramUserService.update_user_tokens_in_telegram_user(
            session, user_id, access_token, refresh_token
        )

    @classmethod
    async def get_or_create_user(
        cls,
        session: AsyncSession,
        client: httpx.AsyncClient,
        username: str,
        password: str,
    ) -> tuple[User, str, str]:
        """
        Retrieve or create a het user and return with tokens.
        """

        if not username:
            raise ValidationError(l_("Username is required"))
        if not password:
            raise ValidationError(l_("Password is required"))

        access_token, refresh_token = await cls.verify_het_account(
            client, username, password
        )

        # check if het user already exists
        existing_user = await cls.get_user(session, username=username)
        if existing_user:
            is_password_correct = password_encoder.verify_password_encoding(
                password, existing_user.password
            )
            if not is_password_correct:
                raise ValidationError(l_("Password is incorrect"))

            # Note: caller is responsible for updating tokens in UserInTelegramUser
            return existing_user, access_token, refresh_token

        encoded_password = password_encoder.get_password_encoding(password)
        user = User(username=username, password=encoded_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, access_token, refresh_token

    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: UUID) -> bool:
        """
        Delete a user by ID.
        """
        delete_statement = delete(User).where(User.id == user_id)
        await session.execute(delete_statement)
        await session.commit()


class TelegramUserService:
    """
    TelegramUserService class for handling database operations related to Telegram users.
    """

    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> list[TelegramUser]:
        """
        Get all telegram users with their linked HET accounts.

        Args:
            session (AsyncSession): The database session.

        Returns:
            list[TelegramUser]: List of all telegram users.
        """
        query = select(TelegramUser).options(
            joinedload(TelegramUser.users).joinedload(UserInTelegramUser.user)
        )
        result = await session.execute(query)
        return result.scalars().unique().all()

    @classmethod
    async def get_user(cls, session: AsyncSession, **fields) -> User:
        """
        Get a user by fields.

        Args:
            session (AsyncSession): The database session.

        Returns:
            User: The user object.
        """
        where_clause = [
            getattr(TelegramUser, key) == value for key, value in fields.items()
        ]

        # optimize query and get get rid off N+1
        query = (
            select(TelegramUser)
            .options(
                selectinload(TelegramUser.users).selectinload(UserInTelegramUser.user)
            )
            .where(*where_clause)
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def update_user_tokens_in_telegram_user(
        cls, session: AsyncSession, user_id: UUID, access_token: str, refresh_token: str
    ):
        """
        Updates only users tokens in linked model.
        """
        update_query = (
            update(UserInTelegramUser)
            .where(UserInTelegramUser.user_id == user_id)
            .values(access_token=access_token, refresh_token=refresh_token)
        )
        await session.execute(update_query)
        await session.commit()

    @classmethod
    async def get_user_in_telegram_user(
        cls, session: AsyncSession, user_id: UUID, telegram_user_id: UUID
    ):
        """
        Retrieve a user in telegram user by user_id and telegram_user_id.
        """
        query = (
            select(UserInTelegramUser)
            .options(
                joinedload(UserInTelegramUser.user),
                joinedload(UserInTelegramUser.telegram_user),
            )
            .where(
                UserInTelegramUser.user_id == user_id,
                UserInTelegramUser.telegram_user_id == telegram_user_id,
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_user_language(cls, session: AsyncSession, chat_id: str) -> str:
        """
        Get user's preferred language from database.

        Args:
            session (AsyncSession): Database session
            chat_id (str): Telegram chat ID

        Returns:
            str: Language code (default: "en")
        """
        user = await cls.get_user(session, chat_id=chat_id)
        if user and hasattr(user, "language"):
            return user.language
        return "en"  # Default language

    @classmethod
    async def get_or_create_user(
        cls,
        session: AsyncSession,
        chat_id: str,
        username: str | None = None,
        language: str = "en",
    ) -> TelegramUser:
        """
        Create a new telegram user in database.
        """
        if not chat_id:
            raise ValidationError(l_("Chat ID is required"))

        # check if telegram user already exists
        existing_user = await cls.get_user(session, chat_id=chat_id)
        if existing_user:
            # Update language and username if they changed
            changed = False
            # ONLY update language if it's currently default/unset and a new one is provided
            # This prevents overwriting user-selected language with Telegram's language_code
            if existing_user.language == "en" and language != "en":
                existing_user.language = language
                changed = True

            if username and existing_user.username != username:
                existing_user.username = username
                changed = True

            if changed:
                await session.commit()
                await session.refresh(existing_user)

            return existing_user

        # fallback for username if it is None (Telegram allows no username)
        # we strictly need a username in the database
        if not username:
            username = "unknown"

        user = TelegramUser(chat_id=chat_id, username=username, language=language)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def add_user(
        cls,
        session: AsyncSession,
        chat_id: str,
        client: httpx.AsyncClient,
        het_username: str,
        het_password: str,
    ):
        """
        Find or create a user in database and link it to a telegram user.

        When adding users we expect username and password to be authenticated by HET.
        """
        if not chat_id:
            raise ValidationError(l_("Chat ID is required"))

        telegram_user = await cls.get_user(session, chat_id=chat_id)
        if not telegram_user:
            raise ValidationError(l_("Telegram user not found"))

        # check if user already linked to telegram user
        existing_user_query = await session.execute(
            select(TelegramUser)
            .join(TelegramUser.users)
            .join(UserInTelegramUser.user)
            .where(
                User.username == het_username,
                UserInTelegramUser.telegram_user_id == telegram_user.id,
            )
        )
        existing_user = existing_user_query.scalar_one_or_none()

        if existing_user:
            raise ValidationError(l_("User already linked to this telegram user"))

        user, access_token, refresh_token = await UserService.get_or_create_user(
            session, client, het_username, het_password
        )

        user_in_telegram_user = UserInTelegramUser(
            user_id=user.id,
            telegram_user_id=telegram_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        session.add(user_in_telegram_user)
        await session.commit()
        await session.refresh(user_in_telegram_user)

        return user

    @classmethod
    async def remove_user(cls, session: AsyncSession, chat_id: str, user_id: UUID):
        """
        In remove scenario we expect exact id instead of username.
        Delete the link between user and telegram user.
        """
        if not chat_id:
            raise ValidationError(l_("Chat ID is required"))
        if not user_id:
            raise ValidationError(l_("User ID is required"))

        telegram_user_subquery = (
            select(TelegramUser.id)
            .where(TelegramUser.chat_id == chat_id)
            .scalar_subquery()
        )
        user_subquery = select(User.id).where(User.id == user_id).scalar_subquery()
        delete_query = delete(UserInTelegramUser).where(
            UserInTelegramUser.user_id == user_subquery,
            UserInTelegramUser.telegram_user_id == telegram_user_subquery,
        )

        await session.execute(delete_query)
        await session.commit()
