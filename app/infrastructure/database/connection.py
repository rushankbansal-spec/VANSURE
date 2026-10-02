"""Database infrastructure module.

Provides async SQLAlchemy engine, session management, and base models.
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import (
    DateTime,
    String,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

from app.core.config import get_database_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models with type annotations."""

    # Name of the default "primary key" column.
    __abstract__ = True
    
    # Convention for primary key column names
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


# Type annotations for common column types
str255: Annotated[str, String(255)]
str1000: Annotated[str, String(1000)]
datetime_tz: Annotated[datetime, DateTime(timezone=True), func.now()]


def get_engine() -> AsyncEngine:
    """Create and return the async database engine."""
    settings = get_database_settings()
    return create_async_engine(
        settings.async_url,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_pre_ping=settings.pool_pre_ping,
        connect_args=settings.connect_args,
    )


# Create engine instance
engine = get_engine()

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """FastAPI dependency that provides an async session."""
    async with async_session_factory() as session:
        yield session


# For synchronous operations (migrations, seeding)
sync_sessionmaker = sessionmaker(bind=engine.sync_engine)


def get_sync_session() -> sessionmaker:
    """Get synchronous session maker for non-async operations."""
    return sync_sessionmaker