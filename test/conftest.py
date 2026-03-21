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
from app.db.db_connection import Base, get_db
from app.utils import auth as auth_mod
from app.utils.rbac import RBACService

# Fixed user id for permission-gated routes (JWT override)
TEST_AUTH_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture(autouse=True)
def _grant_all_permissions(monkeypatch):
    """RBAC checks hit the DB; short-circuit so tests need not seed role_permissions."""

    async def _always(self, user_id: UUID, permission_code: str) -> bool:
        return True

    monkeypatch.setattr(RBACService, "has_permission", _always)


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
    """
    test_database_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with test DB + fake authenticated user for RBAC-gated routes."""

    async def override_get_db():
        yield test_db_session

    async def override_get_current_user_id() -> UUID:
        return TEST_AUTH_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_mod.get_current_user_id] = override_get_current_user_id

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

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
        "is_active": True,
    }


@pytest.fixture
def sample_permission_data() -> dict:
    """Sample permission data for testing."""
    return {
        "name": "TEST_PERMISSION",
        "description": "Test permission description",
        "is_active": True,
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing (matches UserCreateRequest)."""
    return {
        "full_name": "Test User",
        "mobile_number": "9876543210",
        "email": "testuser@example.com",
        "password": "testpass123",
        "is_active": True,
    }


@pytest.fixture
def sample_medicine_category_data() -> dict:
    """Sample medicine category for testing."""
    return {
        "name": "Test Category",
        "description": "Test category description",
        "is_active": True,
    }


@pytest.fixture
def sample_brand_master_data() -> dict:
    """Sample shared brand row for /api/v1/brands."""
    return {
        "name": "Test Brand Line",
        "description": "Test brand description",
        "is_active": True,
    }


@pytest.fixture
def sample_medicine_brand_data() -> dict:
    """Fields merged with medicine_id + brand_id in medicine-brand offering tests."""
    return {
        "manufacturer": "Test Manufacturer",
        "is_active": True,
    }


@pytest.fixture
def sample_medicine_data() -> dict:
    """Placeholder; tests must set medicine_category_id after creating a category."""
    return {
        "name": "Test Medicine",
        "description": "Test medicine description",
        "is_active": True,
    }


@pytest.fixture
def sample_order_data() -> dict:
    """Minimal valid order payload."""
    return {
        "customer_phone": "9876543210",
        "delivery_address": "1 Test Street",
        "order_status": "PENDING",
        "total_amount": "100.00",
        "discount_amount": "0.00",
        "delivery_fee": "0.00",
        "final_amount": "100.00",
        "payment_method": "CASH",
    }


@pytest.fixture
def sample_payment_data() -> dict:
    """Sample payment data for testing."""
    return {
        "payment_method": "CASH",
        "payment_status": "PENDING",
        "amount": "100.00",
    }
