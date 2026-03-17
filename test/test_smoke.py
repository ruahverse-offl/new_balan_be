import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok():
    from main import app
    from app.db.db_connection import DatabaseConnection

    # When using ASGI test client, startup events may not run depending on transport.
    # Ensure DB is initialized for endpoints that depend on get_db().
    DatabaseConnection.initialize()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") in ("healthy", "unhealthy")


@pytest.mark.asyncio
async def test_register_login_and_rbac_blocks_customer_update():
    from main import app
    from app.db.db_connection import DatabaseConnection
    import time

    DatabaseConnection.initialize()

    email = f"pytest_customer_{int(time.time())}@example.com"
    password = "Test@12345"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        reg = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Pytest Customer",
                "mobile_number": "9999999999",
            },
        )
        assert reg.status_code in (200, 201)

        login = await ac.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = (login.json() or {}).get("token") or (login.json() or {}).get("access_token")
        assert token

        meds = await ac.get("/api/v1/medicines/", params={"limit": 1})
        assert meds.status_code == 200
        items = (meds.json() or {}).get("items") or []
        if not items:
            pytest.skip("No medicines seeded; RBAC update test skipped")
        med_id = items[0]["id"]

        # Customer should not be allowed to update medicine availability
        upd = await ac.patch(
            f"/api/v1/medicines/{med_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_available": False},
        )
        assert upd.status_code in (401, 403)


def test_delivery_window_parser_unit():
    from app.utils.delivery_windows import parse_slot_time_label, is_now_within_any_slot
    from datetime import datetime, timezone

    rng = parse_slot_time_label("9:00 AM - 11:00 AM")
    assert rng is not None
    assert rng.start == 9 * 60
    assert rng.end == 11 * 60

    # 03:00 UTC == 08:30 IST -> outside 9-11 slot
    outside = datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)
    assert is_now_within_any_slot(["9:00 AM - 11:00 AM"], now=outside) is False

