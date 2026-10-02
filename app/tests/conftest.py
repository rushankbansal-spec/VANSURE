"""Pytest configuration and fixtures for VanSure backend tests."""

import asyncio
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asyncpg import Connection
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.tenant_context import TenantContext
from app.infrastructure.database import Base


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/vansure_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test database setup
# ============================================================================

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Create test database if it doesn't exist
    sync_engine = engine.sync_engine
    async with sync_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield engine


@pytest_asyncio.fixture(scope="session")
async def create_test_database(test_engine):
    """Create test database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="function")
async def db_session(create_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session for each test."""
    async with async_session_factory() as session:
        yield session
        # Rollback after each test
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def clean_db(db_session: AsyncSession):
    """Clean database before each test."""
    # Clear tenant context
    TenantContext.clear()
    yield db_session


# ============================================================================
# Tenant context fixture
# ============================================================================

@pytest.fixture
def tenant_context():
    """Fixture for tenant context.

    Usage:
        def test_something(clean_db, tenant_context):
            with tenant_context("school-123"):
                ...
    """

    class TenantContextManager:
        def __enter__(self, school_id: str = "test-school"):
            TenantContext.set_tenant(school_id, "test-user")
            return school_id

        def __exit__(self, exc_type, exc_val, exc_tb):
            TenantContext.clear()
            return False

    return TenantContextManager()


# ============================================================================
# Configuration fixture
# ============================================================================

@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        app_name="VanSure Test",
        debug=True,
        database={"url": "sqlite+aiosqlite:///test.db", "echo": False},
        redis={"dsn": "redis://localhost:6379/15"},
    )