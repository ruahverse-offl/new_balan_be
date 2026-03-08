"""
Test suite for Payments CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestPaymentsCRUD:
    """Test all CRUD operations for Payments."""
    
    async def test_create_payment(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test creating a new payment."""
        # Create role, user, and order first
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "order_source": "PRESCRIPTION",
            "order_status": "PENDING",
            "approval_status": "PENDING"
        }
        order_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = order_resp.json()["id"]
        
        # Create payment
        payment_data = {
            "order_id": str(order_id),
            "payment_method": "CASH",
            "payment_status": "PENDING",
            "amount": "100.00"
        }
        response = await test_client.post("/api/v1/payments/", json=payment_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == str(order_id)
        assert data["payment_method"] == "CASH"
        assert data["payment_status"] == "PENDING"
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_payment_by_id(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting a payment by ID."""
        # Create role, user, order, and payment
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "order_source": "PRESCRIPTION",
            "order_status": "PENDING",
            "approval_status": "PENDING"
        }
        order_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = order_resp.json()["id"]
        
        payment_data = {
            "order_id": str(order_id),
            "payment_method": "CASH",
            "payment_status": "PENDING",
            "amount": "100.00"
        }
        create_resp = await test_client.post("/api/v1/payments/", json=payment_data)
        payment_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/payments/{payment_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payment_id
    
    async def test_get_payments_list(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of payments."""
        # Create role
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create multiple users, orders, and payments
        for i in range(3):
            user_data = {
                **sample_user_data,
                "role_id": str(role_id),
                "email": f"customer{i}@example.com",
                "username": f"customer{i}"
            }
            user_resp = await test_client.post("/api/v1/users/", json=user_data)
            user_id = user_resp.json()["id"]
            
            order_data = {
                "customer_id": str(user_id),
                "order_source": "PRESCRIPTION",
                "order_status": "PENDING",
                "approval_status": "PENDING"
            }
            order_resp = await test_client.post("/api/v1/orders/", json=order_data)
            order_id = order_resp.json()["id"]
            
            payment_data = {
                "order_id": str(order_id),
                "payment_method": "CASH",
                "payment_status": "PENDING",
                "amount": "100.00"
            }
            await test_client.post("/api/v1/payments/", json=payment_data)
        
        response = await test_client.get("/api/v1/payments/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_get_payments_list_with_search(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of payments with search."""
        # Create role, user, order, and payment
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "order_source": "PRESCRIPTION",
            "order_status": "PENDING",
            "approval_status": "PENDING"
        }
        order_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = order_resp.json()["id"]
        
        payment_data = {
            "order_id": str(order_id),
            "payment_method": "CASH",
            "payment_status": "PENDING",
            "amount": "100.00"
        }
        await test_client.post("/api/v1/payments/", json=payment_data)
        
        # Search
        response = await test_client.get("/api/v1/payments/?search=CASH")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("CASH" in item["payment_method"] for item in data["items"])
    
    async def test_update_payment(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test updating a payment."""
        # Create role, user, order, and payment
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "order_source": "PRESCRIPTION",
            "order_status": "PENDING",
            "approval_status": "PENDING"
        }
        order_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = order_resp.json()["id"]
        
        payment_data = {
            "order_id": str(order_id),
            "payment_method": "CASH",
            "payment_status": "PENDING",
            "amount": "100.00"
        }
        create_resp = await test_client.post("/api/v1/payments/", json=payment_data)
        payment_id = create_resp.json()["id"]
        
        update_data = {"payment_status": "COMPLETED"}
        response = await test_client.patch(f"/api/v1/payments/{payment_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["payment_status"] == "COMPLETED"
        assert "updated_by" in data
    
    async def test_delete_payment(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test soft deleting a payment."""
        # Create role, user, order, and payment
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        order_data = {
            "customer_id": str(user_id),
            "order_source": "PRESCRIPTION",
            "order_status": "PENDING",
            "approval_status": "PENDING"
        }
        order_resp = await test_client.post("/api/v1/orders/", json=order_data)
        order_id = order_resp.json()["id"]
        
        payment_data = {
            "order_id": str(order_id),
            "payment_method": "CASH",
            "payment_status": "PENDING",
            "amount": "100.00"
        }
        create_resp = await test_client.post("/api/v1/payments/", json=payment_data)
        payment_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/payments/{payment_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
