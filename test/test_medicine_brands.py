"""
Test suite for medicine–brand offerings (/medicine-brands); reads via /medicines.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMedicineBrandsCRUD:
    """Create/update/delete offerings; list/detail via medicines API."""

    async def _seed_medicine_and_brand(self, test_client: AsyncClient):
        cat_resp = await test_client.post(
            "/api/v1/medicine-categories/",
            json={"name": "Cat", "description": "d", "is_active": True},
        )
        cid = cat_resp.json()["id"]
        med_resp = await test_client.post(
            "/api/v1/medicines/",
            json={
                "name": "Med",
                "medicine_category_id": cid,
                "is_prescription_required": False,
                "is_available": True,
            },
        )
        mid = med_resp.json()["id"]
        brand_resp = await test_client.post(
            "/api/v1/brands/",
            json={"name": "LineBrand", "description": None, "is_active": True},
        )
        bid = brand_resp.json()["id"]
        return mid, bid

    async def test_create_medicine_brand(
        self,
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
    ):
        medicine_id, brand_id = await self._seed_medicine_and_brand(test_client)

        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "brand_id": str(brand_id),
            "mrp": "25.50",
        }
        response = await test_client.post("/api/v1/medicine-brands/", json=brand_data)

        assert response.status_code == 201
        data = response.json()
        assert data["brand_name"] == "LineBrand"
        assert data["medicine_id"] == str(medicine_id)
        assert data["brand_id"] == str(brand_id)
        assert "id" in data
        assert data["is_deleted"] is False

    async def test_get_medicine_brand_via_medicine_detail(
        self,
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
    ):
        medicine_id, brand_id = await self._seed_medicine_and_brand(test_client)

        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "brand_id": str(brand_id),
            "mrp": "25.50",
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        offering_id = create_resp.json()["id"]

        response = await test_client.get(
            f"/api/v1/medicines/{medicine_id}", params={"include_brands": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == medicine_id
        assert "brands" in data
        ids = [b["id"] for b in data["brands"]]
        assert offering_id in ids

    async def test_get_medicine_brands_via_medicines_list(
        self,
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
    ):
        medicine_id, brand_id = await self._seed_medicine_and_brand(test_client)

        for i in range(3):
            br = await test_client.post(
                "/api/v1/brands/",
                json={"name": f"ExtraBrand{i}", "is_active": True},
            )
            bid = br.json()["id"]
            await test_client.post(
                "/api/v1/medicine-brands/",
                json={
                    **sample_medicine_brand_data,
                    "medicine_id": str(medicine_id),
                    "brand_id": str(bid),
                    "mrp": "25.50",
                },
            )

        response = await test_client.get(
            "/api/v1/medicines/", params={"limit": 10, "offset": 0, "include_brands": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        med = next((m for m in data["items"] if m["id"] == medicine_id), None)
        assert med is not None
        assert len(med.get("brands") or []) >= 3

    async def test_update_medicine_brand(
        self,
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
    ):
        medicine_id, brand_id = await self._seed_medicine_and_brand(test_client)

        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "brand_id": str(brand_id),
            "mrp": "25.50",
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        offering_id = create_resp.json()["id"]

        update_data = {"manufacturer": "Updated Mfg", "mrp": "30.00"}
        response = await test_client.patch(f"/api/v1/medicine-brands/{offering_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["manufacturer"] == "Updated Mfg"

    async def test_delete_medicine_brand(
        self,
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
    ):
        medicine_id, brand_id = await self._seed_medicine_and_brand(test_client)

        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "brand_id": str(brand_id),
            "mrp": "25.50",
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        offering_id = create_resp.json()["id"]

        response = await test_client.delete(f"/api/v1/medicine-brands/{offering_id}")

        assert response.status_code == 200
        assert "message" in response.json()
