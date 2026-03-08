"""
Test suite for Medicine Brands CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from decimal import Decimal


@pytest.mark.asyncio
class TestMedicineBrandsCRUD:
    """Test all CRUD operations for Medicine Brands."""
    
    async def test_create_medicine_brand(
        self, 
        test_client: AsyncClient, 
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test creating a new medicine brand."""
        # Create medicine first
        med_resp = await test_client.post("/api/v1/medicines/", json=sample_medicine_data)
        medicine_id = med_resp.json()["id"]
        
        # Create brand
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        response = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["brand_name"] == sample_medicine_brand_data["brand_name"]
        assert data["medicine_id"] == str(medicine_id)
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_medicine_brand_by_id(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test getting a medicine brand by ID."""
        # Create medicine and brand
        med_resp = await test_client.post("/api/v1/medicines/", json=sample_medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/medicine-brands/{brand_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == brand_id
    
    async def test_get_medicine_brands_list(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test getting list of medicine brands."""
        # Create medicine
        med_resp = await test_client.post("/api/v1/medicines/", json=sample_medicine_data)
        medicine_id = med_resp.json()["id"]
        
        # Create multiple brands
        for i in range(3):
            brand_data = {
                **sample_medicine_brand_data,
                "medicine_id": str(medicine_id),
                "brand_name": f"Brand_{i}",
                "mrp": "25.50"
            }
            await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        
        response = await test_client.get("/api/v1/medicine-brands/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_medicine_brand(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test updating a medicine brand."""
        # Create medicine and brand
        med_resp = await test_client.post("/api/v1/medicines/", json=sample_medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = create_resp.json()["id"]
        
        update_data = {"brand_name": "Updated Brand", "mrp": "30.00"}
        response = await test_client.patch(f"/api/v1/medicine-brands/{brand_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["brand_name"] == "Updated Brand"
    
    async def test_delete_medicine_brand(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test soft deleting a medicine brand."""
        # Create medicine and brand
        med_resp = await test_client.post("/api/v1/medicines/", json=sample_medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        create_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/medicine-brands/{brand_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
