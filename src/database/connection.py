import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from src.core.config import settings


logger = logging.getLogger(__name__)

engine = create_async_engine(str(settings.SQL_DATABASE_URI))
session_pool = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
