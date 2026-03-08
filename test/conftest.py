"""
Pytest configuration and fixtures for testing
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from uuid import UUID, uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.db.db_connection import Base, get_db, DatabaseConnection
from app.db.models import (
    Role, Permission, RolePermission, User, PharmacistProfile,
    TherapeuticCategory, MedicineComposition, MedicineBrand, Medicine,
    ProductBatch, InventoryTransaction, Order, Payment
)


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with in-memory SQLite.
    
    This fixture creates a fresh database for each test function,
    runs migrations, and cleans up after the test.
    """
    # Create async engine for SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create session
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client for FastAPI.
    
    This fixture overrides the database dependency to use the test database.
    """
    # Override database dependency
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id() -> UUID:
    """Generate a test user ID for authentication."""
    return uuid4()


@pytest.fixture
def test_ip_address() -> str:
    """Return a test IP address."""
    return "127.0.0.1"


@pytest.fixture
def sample_role_data() -> dict:
    """Sample role data for testing."""
    return {
        "name": "TEST_ROLE",
        "description": "Test role description",
        "is_active": True
    }


@pytest.fixture
def sample_permission_data() -> dict:
    """Sample permission data for testing."""
    return {
        "name": "TEST_PERMISSION",
        "description": "Test permission description",
        "is_active": True
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True
    }


@pytest.fixture
def sample_therapeutic_category_data() -> dict:
    """Sample therapeutic category data for testing."""
    return {
        "name": "Test Category",
        "description": "Test category description",
        "is_active": True
    }


@pytest.fixture
def sample_medicine_composition_data() -> dict:
    """Sample medicine composition data for testing."""
    return {
        "name": "Test Composition",
        "description": "Test composition description",
        "is_active": True
    }


@pytest.fixture
def sample_medicine_brand_data() -> dict:
    """Sample medicine brand data for testing."""
    return {
        "name": "Test Brand",
        "manufacturer": "Test Manufacturer",
        "is_active": True
    }


@pytest.fixture
def sample_medicine_data() -> dict:
    """Sample medicine data for testing."""
    return {
        "name": "Test Medicine",
        "description": "Test medicine description",
        "is_active": True
    }


@pytest.fixture
def sample_product_batch_data() -> dict:
    """Sample product batch data for testing."""
    return {
        "batch_number": "BATCH001",
        "manufacturing_date": "2024-01-01",
        "expiry_date": "2025-12-31",
        "quantity": 100,
        "is_active": True
    }


@pytest.fixture
def sample_inventory_transaction_data() -> dict:
    """Sample inventory transaction data for testing."""
    return {
        "transaction_type": "IN",
        "quantity": 50,
        "notes": "Test transaction"
    }


@pytest.fixture
def sample_order_data() -> dict:
    """Sample order data for testing."""
    return {
        "order_status": "PENDING",
        "total_amount": "100.00",
        "notes": "Test order"
    }


@pytest.fixture
def sample_payment_data() -> dict:
    """Sample payment data for testing."""
    return {
        "payment_method": "CASH",
        "payment_status": "PENDING",
        "amount": "100.00"
    }
