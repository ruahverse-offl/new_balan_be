"""Tests for medicine categories CRUD."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMedicineCategoriesCRUD:
    async def test_create_medicine_category(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        response = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_medicine_category_data["name"]

    async def test_get_medicine_category_by_id(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        create_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        cat_id = create_resp.json()["id"]
        response = await test_client.get(f"/api/v1/medicine-categories/{cat_id}")
        assert response.status_code == 200
        assert response.json()["id"] == cat_id

    async def test_get_medicine_categories_list(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        for i in range(3):
            await test_client.post(
                "/api/v1/medicine-categories/",
                json={**sample_medicine_category_data, "name": f"Category_{i}"},
            )
        response = await test_client.get("/api/v1/medicine-categories/?limit=10&offset=0")
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 3

    async def test_update_medicine_category(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        create_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        cat_id = create_resp.json()["id"]
        response = await test_client.patch(
            f"/api/v1/medicine-categories/{cat_id}",
            json={"name": "Updated Category"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Category"

    async def test_delete_medicine_category(
        self,
        test_client: AsyncClient,
        sample_medicine_category_data: dict,
    ):
        create_resp = await test_client.post(
            "/api/v1/medicine-categories/", json=sample_medicine_category_data
        )
        cat_id = create_resp.json()["id"]
        response = await test_client.delete(f"/api/v1/medicine-categories/{cat_id}")
        assert response.status_code == 200
        assert "message" in response.json()
