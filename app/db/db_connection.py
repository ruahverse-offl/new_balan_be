"""
Async SQLAlchemy engine, session factory, and FastAPI ``get_db`` dependency.

Supports:
- **DATABASE_URL**: ``postgresql+asyncpg://...`` (local or public IP).
- **Cloud SQL Connector**: ``INSTANCE_CONNECTION_NAME`` + ``DB_*`` (Cloud Run + unix socket / connector).
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseConnection:
    """Holds async engine, session factory, and optional Cloud SQL ``Connector``."""

    _engine = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    _connector = None

    @classmethod
    def initialize(cls) -> None:
        """
        Create the async engine and session factory (idempotent).

        Call once at application startup (or first ``get_db`` use).
        """
        if cls._engine is not None:
            return

        settings = get_settings()

        if settings.uses_cloud_sql_connector():
            from google.cloud.sql.connector import Connector

            cls._connector = Connector()

            async def _async_creator():
                return await cls._connector.connect_async(
                    settings.INSTANCE_CONNECTION_NAME,
                    "asyncpg",
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    db=settings.DB_NAME,
                )

            cls._engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=_async_creator,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
            )
            logger.info(
                "Database engine created (Cloud SQL connector, instance=%s)",
                settings.INSTANCE_CONNECTION_NAME,
            )
        else:
            cls._engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
            )
            logger.info("Database engine created (DATABASE_URL)")

        cls._session_factory = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        if cls._session_factory is None:
            raise RuntimeError("Database not initialized; call DatabaseConnection.initialize() first")
        return cls._session_factory

    @classmethod
    async def is_connected(cls) -> bool:
        """Return True if a simple ``SELECT 1`` succeeds."""
        if cls._engine is None:
            return False
        try:
            async with cls._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("Database ping failed: %s", exc)
            return False

    @classmethod
    async def create_tables(cls) -> None:
        """Create all tables registered on ``Base`` (idempotent for existing tables)."""
        if cls._engine is None:
            raise RuntimeError("Database not initialized")

        from app.db import models  # noqa: F401 — register models with metadata

        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (create_all)")

    @classmethod
    async def close(cls) -> None:
        """Dispose engine and close Cloud SQL connector if used."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
        if cls._connector is not None:
            await cls._connector.close_async()
            cls._connector = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an ``AsyncSession`` and commits on success.

    Ensures ``DatabaseConnection.initialize()`` has run.
    """
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
