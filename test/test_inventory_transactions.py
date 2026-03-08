"""
Test suite for Inventory Transactions CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import date, timedelta


@pytest.mark.asyncio
class TestInventoryTransactionsCRUD:
    """Test all CRUD operations for Inventory Transactions."""
    
    async def test_create_inventory_transaction(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test creating a new inventory transaction."""
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
        batch_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = batch_resp.json()["id"]
        
        # Create inventory transaction
        transaction_data = {
            "medicine_brand_id": str(brand_id),
            "product_batch_id": str(batch_id),
            "transaction_type": "SALE",
            "quantity_change": -10,
            "remarks": "Sold to customer"
        }
        response = await test_client.post("/api/v1/inventory-transactions/", json=transaction_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "SALE"
        assert data["quantity_change"] == -10
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_inventory_transaction_by_id(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test getting an inventory transaction by ID."""
        # Setup (same as above)
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
        batch_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = batch_resp.json()["id"]
        
        transaction_data = {
            "medicine_brand_id": str(brand_id),
            "product_batch_id": str(batch_id),
            "transaction_type": "SALE",
            "quantity_change": -10,
            "remarks": "Sold to customer"
        }
        create_resp = await test_client.post("/api/v1/inventory-transactions/", json=transaction_data)
        transaction_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/inventory-transactions/{transaction_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
    
    async def test_get_inventory_transactions_list(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test getting list of inventory transactions."""
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
        batch_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = batch_resp.json()["id"]
        
        # Create multiple transactions
        for i in range(3):
            transaction_data = {
                "medicine_brand_id": str(brand_id),
                "product_batch_id": str(batch_id),
                "transaction_type": "SALE",
                "quantity_change": -10,
                "remarks": f"Transaction {i}"
            }
            await test_client.post("/api/v1/inventory-transactions/", json=transaction_data)
        
        response = await test_client.get("/api/v1/inventory-transactions/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_inventory_transaction(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test updating an inventory transaction."""
        # Setup (same pattern)
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
        batch_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = batch_resp.json()["id"]
        
        transaction_data = {
            "medicine_brand_id": str(brand_id),
            "product_batch_id": str(batch_id),
            "transaction_type": "SALE",
            "quantity_change": -10,
            "remarks": "Sold to customer"
        }
        create_resp = await test_client.post("/api/v1/inventory-transactions/", json=transaction_data)
        transaction_id = create_resp.json()["id"]
        
        update_data = {"remarks": "Updated remarks"}
        response = await test_client.patch(f"/api/v1/inventory-transactions/{transaction_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["remarks"] == "Updated remarks"
    
    async def test_delete_inventory_transaction(
        self, 
        test_client: AsyncClient,
        sample_medicine_brand_data: dict
    ):
        """Test soft deleting an inventory transaction."""
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
        batch_resp = await test_client.post("/api/v1/product-batches/", json=batch_data)
        batch_id = batch_resp.json()["id"]
        
        transaction_data = {
            "medicine_brand_id": str(brand_id),
            "product_batch_id": str(batch_id),
            "transaction_type": "SALE",
            "quantity_change": -10,
            "remarks": "Sold to customer"
        }
        create_resp = await test_client.post("/api/v1/inventory-transactions/", json=transaction_data)
        transaction_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/inventory-transactions/{transaction_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
