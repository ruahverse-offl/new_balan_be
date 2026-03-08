"""
Test suite for Product Batches CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import date, timedelta


@pytest.mark.asyncio
class TestProductBatchesCRUD:
    """Test all CRUD operations for Product Batches."""
    
    async def test_create_product_batch(
        self, 
        test_client: AsyncClient, 
        sample_medicine_brand_data: dict,
        sample_medicine_data: dict
    ):
        """Test creating a new product batch."""
        # Create medicine and brand first
        # Create therapeutic category
        from test.conftest import sample_therapeutic_category_data
        cat_data = {"name": "Test Category", "description": "Test", "is_active": True}
        cat_resp = await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        category_id = cat_resp.json()["id"]
        
        # Create medicine
        medicine_data = {
            "name": "Test Medicine",
            "dosage_form": "Tablet",
            "therapeutic_category_id": str(category_id),
            "is_prescription_required": False,
            "is_controlled": False,
            "schedule_type": "OTC",
            "is_active": True
        }
        med_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = med_resp.json()["id"]
        
        # Create brand
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        brand_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = brand_resp.json()["id"]
        
        # Create product batch
        batch_data = {
            "medicine_brand_id": str(brand_id),
            "batch_number": "BATCH001",
            "expiry_date": str(date.today() + timedelta(days=365)),
            "purchase_price": "18.50",
            "quantity_available": 100
        }
        response = await test_client.post("/api/v1/product-batches/", json=batch_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["batch_number"] == "BATCH001"
        assert data["medicine_brand_id"] == str(brand_id)
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_product_batch_by_id(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test getting a product batch by ID."""
        # Setup: create category, medicine, brand, and batch
        cat_data = {"name": "Test Category", "description": "Test", "is_active": True}
        cat_resp = await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        category_id = cat_resp.json()["id"]
        
        medicine_data = {
            "name": "Test Medicine",
            "dosage_form": "Tablet",
            "therapeutic_category_id": str(category_id),
            "is_prescription_required": False,
            "is_controlled": False,
            "schedule_type": "OTC",
            "is_active": True
        }
        med_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        brand_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = brand_resp.json()["id"]
        
        batch_data = {
            "medicine_brand_id": str(brand_id),
            "batch_number": "BATCH001",
            "expiry_date": str(date.today() + timedelta(days=365)),
            "purchase_price": "18.50",
            "quantity_available": 100
        }
        create_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/product-batches/{batch_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == batch_id
    
    async def test_get_product_batches_list(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test getting list of product batches."""
        # Setup
        cat_data = {"name": "Test Category", "description": "Test", "is_active": True}
        cat_resp = await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        category_id = cat_resp.json()["id"]
        
        medicine_data = {
            "name": "Test Medicine",
            "dosage_form": "Tablet",
            "therapeutic_category_id": str(category_id),
            "is_prescription_required": False,
            "is_controlled": False,
            "schedule_type": "OTC",
            "is_active": True
        }
        med_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        brand_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = brand_resp.json()["id"]
        
        # Create multiple batches
        for i in range(3):
            batch_data = {
                "medicine_brand_id": str(brand_id),
                "batch_number": f"BATCH00{i}",
                "expiry_date": str(date.today() + timedelta(days=365)),
                "purchase_price": "18.50",
                "quantity_available": 100
            }
            await test_client.post("/api/v1/product-batches/", json=batch_data)
        
        response = await test_client.get("/api/v1/product-batches/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_product_batch(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test updating a product batch."""
        # Setup
        cat_data = {"name": "Test Category", "description": "Test", "is_active": True}
        cat_resp = await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        category_id = cat_resp.json()["id"]
        
        medicine_data = {
            "name": "Test Medicine",
            "dosage_form": "Tablet",
            "therapeutic_category_id": str(category_id),
            "is_prescription_required": False,
            "is_controlled": False,
            "schedule_type": "OTC",
            "is_active": True
        }
        med_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        brand_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = brand_resp.json()["id"]
        
        batch_data = {
            "medicine_brand_id": str(brand_id),
            "batch_number": "BATCH001",
            "expiry_date": str(date.today() + timedelta(days=365)),
            "purchase_price": "18.50",
            "quantity_available": 100
        }
        create_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = create_resp.json()["id"]
        
        update_data = {"quantity_available": 150}
        response = await test_client.patch(f"/api/v1/product-batches/{batch_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity_available"] == 150
    
    async def test_delete_product_batch(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test soft deleting a product batch."""
        # Setup
        cat_data = {"name": "Test Category", "description": "Test", "is_active": True}
        cat_resp = await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        category_id = cat_resp.json()["id"]
        
        medicine_data = {
            "name": "Test Medicine",
            "dosage_form": "Tablet",
            "therapeutic_category_id": str(category_id),
            "is_prescription_required": False,
            "is_controlled": False,
            "schedule_type": "OTC",
            "is_active": True
        }
        med_resp = await test_client.post("/api/v1/medicines/", json=medicine_data)
        medicine_id = med_resp.json()["id"]
        
        brand_data = {
            **sample_medicine_brand_data,
            "medicine_id": str(medicine_id),
            "mrp": "25.50"
        }
        brand_resp = await test_client.post("/api/v1/medicine-brands/", json=brand_data)
        brand_id = brand_resp.json()["id"]
        
        batch_data = {
            "medicine_brand_id": str(brand_id),
            "batch_number": "BATCH001",
            "expiry_date": str(date.today() + timedelta(days=365)),
            "purchase_price": "18.50",
            "quantity_available": 100
        }
        create_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/product-batches/{batch_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
