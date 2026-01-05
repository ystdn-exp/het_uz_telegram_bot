from uuid import UUID, uuid4

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class BaseModel(DeclarativeBase):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
