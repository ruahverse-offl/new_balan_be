"""
Test suite for Role Permissions CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestRolePermissionsCRUD:
    """Test all CRUD operations for Role Permissions."""
    
    async def test_create_role_permission(
        self, 
        test_client: AsyncClient, 
        sample_role_data: dict,
        sample_permission_data: dict
    ):
        """Test creating a new role permission."""
        # Create role and permission first
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        perm_resp = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = perm_resp.json()["id"]
        
        # Create role permission
        data = {
            "role_id": str(role_id),
            "permission_id": str(permission_id),
            "is_active": True
        }
        response = await test_client.post("/api/v1/role-permissions/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["role_id"] == str(role_id)
        assert result["permission_id"] == str(permission_id)
        assert "id" in result
        assert result["is_deleted"] is False
    
    async def test_get_role_permission_by_id(
        self, 
        test_client: AsyncClient,
        sample_role_data: dict,
        sample_permission_data: dict
    ):
        """Test getting a role permission by ID."""
        # Create role, permission, and role_permission
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        perm_resp = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = perm_resp.json()["id"]
        
        create_data = {
            "role_id": str(role_id),
            "permission_id": str(permission_id),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/role-permissions/", json=create_data)
        rp_id = create_resp.json()["id"]
        
        # Get the role permission
        response = await test_client.get(f"/api/v1/role-permissions/{rp_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rp_id
    
    async def test_get_role_permissions_list(
        self, 
        test_client: AsyncClient,
        sample_role_data: dict,
        sample_permission_data: dict
    ):
        """Test getting list of role permissions."""
        # Create multiple role permissions
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        for i in range(3):
            perm_data = {**sample_permission_data, "code": f"PERM_{i}"}
            perm_resp = await test_client.post("/api/v1/permissions/", json=perm_data)
            permission_id = perm_resp.json()["id"]
            
            rp_data = {
                "role_id": str(role_id),
                "permission_id": str(permission_id),
                "is_active": True
            }
            await test_client.post("/api/v1/role-permissions/", json=rp_data)
        
        # Get list
        response = await test_client.get("/api/v1/role-permissions/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) >= 3
    
    async def test_update_role_permission(
        self, 
        test_client: AsyncClient,
        sample_role_data: dict,
        sample_permission_data: dict
    ):
        """Test updating a role permission."""
        # Create role, permission, and role_permission
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        perm_resp = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = perm_resp.json()["id"]
        
        create_data = {
            "role_id": str(role_id),
            "permission_id": str(permission_id),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/role-permissions/", json=create_data)
        rp_id = create_resp.json()["id"]
        
        # Update
        update_data = {"is_active": False}
        response = await test_client.patch(f"/api/v1/role-permissions/{rp_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert "updated_by" in data
    
    async def test_delete_role_permission(
        self, 
        test_client: AsyncClient,
        sample_role_data: dict,
        sample_permission_data: dict
    ):
        """Test soft deleting a role permission."""
        # Create role, permission, and role_permission
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        perm_resp = await test_client.post("/api/v1/permissions/", json=sample_permission_data)
        permission_id = perm_resp.json()["id"]
        
        create_data = {
            "role_id": str(role_id),
            "permission_id": str(permission_id),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/role-permissions/", json=create_data)
        rp_id = create_resp.json()["id"]
        
        # Delete
        response = await test_client.delete(f"/api/v1/role-permissions/{rp_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
