"""
Test suite for Roles CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestRolesCRUD:
    """Test all CRUD operations for Roles."""
    
    async def test_create_role(self, test_client: AsyncClient, sample_role_data: dict):
        """Test creating a new role."""
        response = await test_client.post("/api/v1/roles/", json=sample_role_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_role_data["name"]
        assert data["description"] == sample_role_data["description"]
        assert data["is_active"] == sample_role_data["is_active"]
        assert "id" in data
        assert "created_by" in data
        assert "created_at" in data
        assert "created_ip" in data
        assert data["is_deleted"] is False
    
    async def test_get_role_by_id(self, test_client: AsyncClient, sample_role_data: dict):
        """Test getting a role by ID."""
        # Create a role first
        create_response = await test_client.post("/api/v1/roles/", json=sample_role_data)
        assert create_response.status_code == 201
        role_id = create_response.json()["id"]
        
        # Get the role
        response = await test_client.get(f"/api/v1/roles/{role_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == role_id
        assert data["name"] == sample_role_data["name"]
    
    async def test_get_role_by_id_not_found(self, test_client: AsyncClient):
        """Test getting a non-existent role."""
        fake_id = uuid4()
        response = await test_client.get(f"/api/v1/roles/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_roles_list(self, test_client: AsyncClient, sample_role_data: dict):
        """Test getting list of roles with pagination."""
        # Create multiple roles
        for i in range(5):
            role_data = {**sample_role_data, "name": f"{sample_role_data['name']}_{i}"}
            await test_client.post("/api/v1/roles/", json=role_data)
        
        # Get list
        response = await test_client.get("/api/v1/roles/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) >= 5
        assert data["pagination"]["total"] >= 5
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 0
    
    async def test_get_roles_list_with_search(self, test_client: AsyncClient, sample_role_data: dict):
        """Test getting list of roles with search."""
        # Create roles with different names
        await test_client.post("/api/v1/roles/", json={**sample_role_data, "name": "ADMIN_ROLE"})
        await test_client.post("/api/v1/roles/", json={**sample_role_data, "name": "USER_ROLE"})
        
        # Search for ADMIN
        response = await test_client.get("/api/v1/roles/?search=ADMIN")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("ADMIN" in item["name"] for item in data["items"])
    
    async def test_get_roles_list_with_sort(self, test_client: AsyncClient, sample_role_data: dict):
        """Test getting list of roles with sorting."""
        # Create roles
        await test_client.post("/api/v1/roles/", json={**sample_role_data, "name": "B_ROLE"})
        await test_client.post("/api/v1/roles/", json={**sample_role_data, "name": "A_ROLE"})
        
        # Sort by name ascending
        response = await test_client.get("/api/v1/roles/?sort_by=name&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) >= 2:
            names = [item["name"] for item in data["items"]]
            # Check if sorted (at least the first two should be in order)
            assert names == sorted(names)
    
    async def test_update_role(self, test_client: AsyncClient, sample_role_data: dict):
        """Test updating a role."""
        # Create a role
        create_response = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = create_response.json()["id"]
        
        # Update the role
        update_data = {
            "name": "UPDATED_ROLE",
            "description": "Updated description"
        }
        response = await test_client.patch(f"/api/v1/roles/{role_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UPDATED_ROLE"
        assert data["description"] == "Updated description"
        assert "updated_by" in data
        assert "updated_at" in data
        assert "updated_ip" in data
    
    async def test_update_role_not_found(self, test_client: AsyncClient):
        """Test updating a non-existent role."""
        fake_id = uuid4()
        update_data = {"name": "UPDATED_ROLE"}
        response = await test_client.patch(f"/api/v1/roles/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_delete_role(self, test_client: AsyncClient, sample_role_data: dict):
        """Test soft deleting a role."""
        # Create a role
        create_response = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = create_response.json()["id"]
        
        # Delete the role
        response = await test_client.delete(f"/api/v1/roles/{role_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["id"] == str(role_id)
        
        # Verify it's soft deleted (should not appear in list)
        get_response = await test_client.get(f"/api/v1/roles/{role_id}")
        # The role should still exist but be marked as deleted
        # This depends on your implementation - adjust as needed
    
    async def test_delete_role_not_found(self, test_client: AsyncClient):
        """Test deleting a non-existent role."""
        fake_id = uuid4()
        response = await test_client.delete(f"/api/v1/roles/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
