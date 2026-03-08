"""
Test suite for Users CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestUsersCRUD:
    """Test all CRUD operations for Users."""
    
    async def test_create_user(
        self, 
        test_client: AsyncClient, 
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test creating a new user."""
        # Create role first
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create user
        user_data = {
            **sample_user_data,
            "role_id": str(role_id)
        }
        response = await test_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["role_id"] == str(role_id)
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_user_by_id(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting a user by ID."""
        # Create role and user
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        create_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = create_resp.json()["id"]
        
        # Get user
        response = await test_client.get(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]
    
    async def test_get_users_list(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of users."""
        # Create role
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create multiple users
        for i in range(3):
            user_data = {
                **sample_user_data,
                "role_id": str(role_id),
                "email": f"user{i}@example.com",
                "username": f"user{i}"
            }
            await test_client.post("/api/v1/users/", json=user_data)
        
        # Get list
        response = await test_client.get("/api/v1/users/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) >= 3
    
    async def test_get_users_list_with_search(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of users with search."""
        # Create role
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create users
        user_data = {
            **sample_user_data,
            "role_id": str(role_id),
            "full_name": "John Doe"
        }
        await test_client.post("/api/v1/users/", json=user_data)
        
        # Search
        response = await test_client.get("/api/v1/users/?search=John")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("John" in item["full_name"] for item in data["items"])
    
    async def test_update_user(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test updating a user."""
        # Create role and user
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        create_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = create_resp.json()["id"]
        
        # Update
        update_data = {"full_name": "Updated Name"}
        response = await test_client.patch(f"/api/v1/users/{user_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert "updated_by" in data
    
    async def test_delete_user(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test soft deleting a user."""
        # Create role and user
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        create_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = create_resp.json()["id"]
        
        # Delete
        response = await test_client.delete(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
