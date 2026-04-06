"""
PostgreSQL Database Connection Module

This module provides database connection functionality for PostgreSQL using SQLAlchemy
with asyncpg. It handles async connection initialization, database engine management,
and connection lifecycle.
"""

from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Base class for declarative models
Base = declarative_base()


class DatabaseConnection:
    """
    PostgreSQL database connection manager.
    
    This class manages the PostgreSQL connection lifecycle using SQLAlchemy async engine.
    It provides async session management and connection pooling.
    """
    
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    
    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the PostgreSQL connection.
        
        Reads DATABASE_URL from config settings.
        Format: postgresql+asyncpg://user:password@host:port/database
        
        Raises:
            SQLAlchemyError: If unable to connect to PostgreSQL
        """
        try:
            settings = get_settings()
            database_url = settings.get_database_url()
            
            if not database_url:
                raise ValueError("DATABASE_URL is required in configuration")
            
            # Connection pool settings
            pool_size = settings.DB_POOL_SIZE
            max_overflow = settings.DB_MAX_OVERFLOW
            
            logger.info(f"Connecting to PostgreSQL database")
            print("[INFO] Connecting to database...")
            
            # Create async engine with connection pooling
            cls._engine = create_async_engine(
                database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                echo=False,
                future=True,
            )
            
            # Create session factory
            cls._session_factory = async_sessionmaker(
                cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            
            logger.info("PostgreSQL engine and session factory created")
            print("[OK] Database engine initialized!")
            
        except SQLAlchemyError as e:
            error_msg = f"[ERROR] Database connection FAILED: {str(e)}"
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"[ERROR] Database connection FAILED: {str(e)}"
            logger.error(f"Unexpected error during PostgreSQL connection: {str(e)}")
            print(error_msg)
            raise
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """
        Get the SQLAlchemy async engine instance.
        
        Returns:
            AsyncEngine: SQLAlchemy async engine instance
            
        Raises:
            RuntimeError: If database connection is not initialized
        """
        if cls._engine is None:
            raise RuntimeError(
                "Database connection not initialized. "
                "Call DatabaseConnection.initialize() first."
            )
        return cls._engine
    
    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        This is an async generator that yields a session and ensures proper cleanup.
        Use it with async context manager or in a dependency injection pattern.
        
        Yields:
            AsyncSession: SQLAlchemy async session
            
        Example:
            async with DatabaseConnection.get_session() as session:
                result = await session.execute(query)
        """
        if cls._session_factory is None:
            raise RuntimeError(
                "Database connection not initialized. "
                "Call DatabaseConnection.initialize() first."
            )
        
        async with cls._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @classmethod
    def get_session_factory(cls) -> async_sessionmaker:
        """
        Get the session factory for creating sessions manually.
        
        Returns:
            async_sessionmaker: Session factory instance
            
        Raises:
            RuntimeError: If database connection is not initialized
        """
        if cls._session_factory is None:
            raise RuntimeError(
                "Database connection not initialized. "
                "Call DatabaseConnection.initialize() first."
            )
        return cls._session_factory
    
    @classmethod
    async def close(cls) -> None:
        """
        Close the database connection and dispose of the engine.
        
        This method should be called during application shutdown to properly
        close all connections and release resources.
        """
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("PostgreSQL connection closed")
    
    @classmethod
    async def is_connected(cls) -> bool:
        """
        Check if the database connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if cls._engine is None:
            print("[ERROR] Database connection check: Engine not initialized")
            return False
        try:
            async with cls._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("[OK] Database connection check: Connected")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection check: Failed - {str(e)}")
            return False
    
    @classmethod
    async def create_tables(cls) -> None:
        """
        Create all database tables if they don't exist.
        
        This method automatically creates all tables defined in the models
        using SQLAlchemy's metadata.create_all(). It only creates tables
        that don't already exist, so it's safe to call multiple times.
        
        Raises:
            RuntimeError: If database connection is not initialized
            SQLAlchemyError: If unable to create tables
        """
        if cls._engine is None:
            raise RuntimeError(
                "Database connection not initialized. "
                "Call DatabaseConnection.initialize() first."
            )
        
        try:
            # Import all models to ensure they're registered with Base.metadata
            # This import ensures all model classes are loaded and registered
            import app.db.models  # noqa: F401
            
            logger.info("Creating database tables if they don't exist...")
            print("[INFO] Creating database tables...")
            
            async with cls._engine.begin() as conn:
                # Use run_sync to execute the synchronous create_all in async context
                await conn.run_sync(cls._create_all_tables)
                # create_all does not ALTER existing tables — add columns that newer models expect (PostgreSQL only).
                if conn.dialect.name == "postgresql":
                    from app.db.order_fulfillment_schema import apply_order_fulfillment_schema

                    await apply_order_fulfillment_schema(conn)
            
            logger.info("Database tables created/verified successfully")
            print("[OK] Database tables created/verified successfully!")
            
        except SQLAlchemyError as e:
            error_msg = f"[ERROR] Failed to create database tables: {str(e)}"
            logger.error(f"Failed to create database tables: {str(e)}")
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"[ERROR] Unexpected error creating database tables: {str(e)}"
            logger.error(f"Unexpected error creating database tables: {str(e)}")
            print(error_msg)
            raise
    
    @staticmethod
    def _create_all_tables(connection):
        """
        Synchronous helper method to create all tables.
        
        This is called from async context using run_sync.
        """
        # Base is already imported at module level
        Base.metadata.create_all(bind=connection, checkfirst=True)


# Convenience function for dependency injection in FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.
    
    This is a convenience function designed for FastAPI dependency injection.
    It yields a session and ensures proper cleanup after the request.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Example usage in FastAPI route:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async for session in DatabaseConnection.get_session():
        yield session
