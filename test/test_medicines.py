"""
Test suite for Medicines CRUD operations
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMedicinesCRUD:
    """Test all CRUD operations for Medicines."""

    async def test_create_medicine(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        category_id = cat_resp.json()["id"]

        medicine_data = {
            "name": "Test Medicine",
            "medicine_category_id": str(category_id),
            "is_prescription_required": False,
            "description": "Test medicine description",
            "is_available": True,
        }
        response = await test_client.post("/api/v1/medicines/", json=medicine_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Medicine"
        assert data["medicine_category_id"] == str(category_id)
        assert "id" in data
        assert data["is_deleted"] is False

    async def test_get_medicine_by_id(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        category_id = cat_resp.json()["id"]

        medicine_data = {
            "name": "Test Medicine",
            "medicine_category_id": str(category_id),
            "is_prescription_required": False,
            "is_available": True,
        }
        create_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = create_resp.json()["id"]

        response = await test_client.get(f"/api/v1/medicines/{medicine_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == medicine_id

    async def test_get_medicines_list(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        category_id = cat_resp.json()["id"]

        for i in range(3):
            medicine_data = {
                "name": f"Medicine_{i}",
                "medicine_category_id": str(category_id),
                "is_prescription_required": False,
                "is_available": True,
            }
            await test_client.post("/api/v1/medicines/", json=medicine_data)

        response = await test_client.get("/api/v1/medicines/?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

    async def test_update_medicine(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        category_id = cat_resp.json()["id"]

        medicine_data = {
            "name": "Test Medicine",
            "medicine_category_id": str(category_id),
            "is_prescription_required": False,
            "is_available": True,
        }
        create_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = create_resp.json()["id"]

        update_data = {"name": "Updated Medicine"}
        response = await test_client.patch(f"/api/v1/medicines/{medicine_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Medicine"

    async def test_delete_medicine(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        category_id = cat_resp.json()["id"]

        medicine_data = {
            "name": "Test Medicine",
            "medicine_category_id": str(category_id),
            "is_prescription_required": False,
            "is_available": True,
        }
        create_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = create_resp.json()["id"]

        response = await test_client.delete(f"/api/v1/medicines/{medicine_id}")

        assert response.status_code == 200
        assert "message" in response.json()
