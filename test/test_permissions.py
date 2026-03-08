"""
Test suite for Permissions CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestPermissionsCRUD:
    """Test all CRUD operations for Permissions."""
    
    async def test_create_permission(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test creating a new permission."""
        response = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == sample_permission_data["code"]
        assert data["description"] == sample_permission_data["description"]
        assert data["is_active"] == sample_permission_data["is_active"]
        assert "id" in data
        assert "created_by" in data
        assert "created_at" in data
        assert "created_ip" in data
        assert data["is_deleted"] is False
    
    async def test_get_permission_by_id(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test getting a permission by ID."""
        # Create a permission first
        create_response = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        assert create_response.status_code == 201
        permission_id = create_response.json()["id"]
        
        # Get the permission
        response = await test_client.get(f"/api/v1/permissions/{permission_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == permission_id
        assert data["code"] == sample_permission_data["code"]
    
    async def test_get_permission_by_id_not_found(self, test_client: AsyncClient):
        """Test getting a non-existent permission."""
        fake_id = uuid4()
        response = await test_client.get(f"/api/v1/permissions/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_permissions_list(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test getting list of permissions with pagination."""
        # Create multiple permissions
        for i in range(5):
            perm_data = {**sample_permission_data, "code": f"{sample_permission_data['code']}_{i}"}
            await test_client.post("/api/v1/permissions/", json=perm_data)
        
        # Get list
        response = await test_client.get("/api/v1/permissions/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) >= 5
        assert data["pagination"]["total"] >= 5
    
    async def test_get_permissions_list_with_search(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test getting list of permissions with search."""
        # Create permissions with different codes
        await test_client.post("/api/v1/permissions/", json={**sample_permission_data, "code": "READ_PERM"})
        await test_client.post("/api/v1/permissions/", json={**sample_permission_data, "code": "WRITE_PERM"})
        
        # Search
        response = await test_client.get("/api/v1/permissions/?search=READ")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("READ" in item["code"] for item in data["items"])
    
    async def test_get_permissions_list_with_sort(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test getting list of permissions with sorting."""
        # Create permissions
        await test_client.post("/api/v1/permissions/", json={**sample_permission_data, "code": "B_PERM"})
        await test_client.post("/api/v1/permissions/", json={**sample_permission_data, "code": "A_PERM"})
        
        # Sort by code ascending
        response = await test_client.get("/api/v1/permissions/?sort_by=code&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) >= 2:
            codes = [item["code"] for item in data["items"]]
            assert codes == sorted(codes)
    
    async def test_update_permission(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test updating a permission."""
        # Create a permission
        create_response = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = create_response.json()["id"]
        
        # Update the permission
        update_data = {
            "code": "UPDATED_PERM",
            "description": "Updated description"
        }
        response = await test_client.patch(f"/api/v1/permissions/{permission_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "UPDATED_PERM"
        assert data["description"] == "Updated description"
        assert "updated_by" in data
        assert "updated_at" in data
        assert "updated_ip" in data
    
    async def test_update_permission_not_found(self, test_client: AsyncClient):
        """Test updating a non-existent permission."""
        fake_id = uuid4()
        update_data = {"code": "UPDATED_PERM"}
        response = await test_client.patch(f"/api/v1/permissions/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_delete_permission(self, test_client: AsyncClient, sample_permission_data: dict):
        """Test soft deleting a permission."""
        # Create a permission
        create_response = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = create_response.json()["id"]
        
        # Delete the permission
        response = await test_client.delete(f"/api/v1/permissions/{permission_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["id"] == str(permission_id)
    
    async def test_delete_permission_not_found(self, test_client: AsyncClient):
        """Test deleting a non-existent permission."""
        fake_id = uuid4()
        response = await test_client.delete(f"/api/v1/permissions/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
