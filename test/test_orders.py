"""
Test suite for Orders CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestOrdersCRUD:
    """Test all CRUD operations for Orders."""
    
    async def test_create_order(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test creating a new order."""
        # Create role and user first
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        # Create order
        order_data = {
            "customer_id": str(user_id),
            "customer_phone": "9876543210",
            "delivery_address": "1 Test St",
            "order_status": "PENDING",
            "total_amount": "100.00",
            "discount_amount": "0.00",
            "delivery_fee": "0.00",
            "final_amount": "100.00",
            "payment_method": "CASH",
        }
        response = await test_client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == str(user_id)
        assert data["order_status"] == "PENDING"
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_order_by_id(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting an order by ID."""
        # Create role, user, and order
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "customer_phone": "9876543210",
            "delivery_address": "1 Test St",
            "order_status": "PENDING",
            "total_amount": "100.00",
            "discount_amount": "0.00",
            "delivery_fee": "0.00",
            "final_amount": "100.00",
            "payment_method": "CASH",
        }
        create_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
    
    async def test_get_orders_list(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of orders."""
        # Create role
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create multiple users and orders
        for i in range(3):
            user_data = {
                **sample_user_data,
                "role_id": str(role_id),
                "email": f"customer{i}@example.com",
                "mobile_number": f"987654321{i}",
            }
            user_resp = await test_client.post("/api/v1/users/", json=user_data)
            user_id = user_resp.json()["id"]
            
            order_data = {
                "customer_id": str(user_id),
                "customer_phone": f"987654321{i}",
                "delivery_address": f"{i} Test St",
                "order_status": "PENDING",
                "total_amount": "100.00",
                "discount_amount": "0.00",
                "delivery_fee": "0.00",
                "final_amount": "100.00",
                "payment_method": "CASH",
            }
            await test_client.post("/api/v1/orders/", json=order_data)
        
        response = await test_client.get("/api/v1/orders/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_get_orders_list_with_search(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of orders with search."""
        # Create role and user
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "customer_phone": "9876543210",
            "delivery_address": "1 Test St",
            "order_status": "PENDING",
            "total_amount": "100.00",
            "discount_amount": "0.00",
            "delivery_fee": "0.00",
            "final_amount": "100.00",
            "payment_method": "CASH",
        }
        await test_client.post("/api/v1/orders/", json=order_data)
        
        # Search
        response = await test_client.get("/api/v1/orders/?search=PENDING")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
    
    async def test_update_order(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test updating an order."""
        # Create role, user, and order
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "customer_phone": "9876543210",
            "delivery_address": "1 Test St",
            "order_status": "PENDING",
            "total_amount": "100.00",
            "discount_amount": "0.00",
            "delivery_fee": "0.00",
            "final_amount": "100.00",
            "payment_method": "CASH",
        }
        create_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = create_resp.json()["id"]
        
        update_data = {
            "order_status": "CANCELLED_BY_STAFF",
            "cancellation_reason": "Test cancellation — invalid prescription",
        }
        response = await test_client.patch(f"/api/v1/orders/{order_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "CANCELLED_BY_STAFF"
        assert data["cancellation_reason"] == "Test cancellation — invalid prescription"
        assert "updated_by" in data
    
    async def test_delete_order(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test soft deleting an order."""
        # Create role, user, and order
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "customer_phone": "9876543210",
            "delivery_address": "1 Test St",
            "order_status": "PENDING",
            "total_amount": "100.00",
            "discount_amount": "0.00",
            "delivery_fee": "0.00",
            "final_amount": "100.00",
            "payment_method": "CASH",
        }
        create_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
