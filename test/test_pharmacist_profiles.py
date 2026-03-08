"""
Test suite for Pharmacist Profiles CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import date, timedelta


@pytest.mark.asyncio
class TestPharmacistProfilesCRUD:
    """Test all CRUD operations for Pharmacist Profiles."""
    
    async def test_create_pharmacist_profile(
        self, 
        test_client: AsyncClient, 
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test creating a new pharmacist profile."""
        # Create role and user first
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        # Create pharmacist profile
        profile_data = {
            "user_id": str(user_id),
            "license_number": "PHARMA-AP-12345",
            "license_valid_till": str(date.today() + timedelta(days=365)),
            "is_active": True
        }
        response = await test_client.post("/api/v1/pharmacist-profiles/", json=profile_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["license_number"] == "PHARMA-AP-12345"
        assert data["user_id"] == str(user_id)
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_pharmacist_profile_by_id(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting a pharmacist profile by ID."""
        # Create role, user, and profile
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        profile_data = {
            "user_id": str(user_id),
            "license_number": "PHARMA-AP-12345",
            "license_valid_till": str(date.today() + timedelta(days=365)),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/pharmacist-profiles/", json=profile_data)
        profile_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/pharmacist-profiles/{profile_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
    
    async def test_get_pharmacist_profiles_list(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test getting list of pharmacist profiles."""
        # Create role
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        # Create multiple users and profiles
        for i in range(3):
            user_data = {
                **sample_user_data,
                "role_id": str(role_id),
                "email": f"pharmacist{i}@example.com",
                "username": f"pharmacist{i}"
            }
            user_resp = await test_client.post("/api/v1/users/", json=user_data)
            user_id = user_resp.json()["id"]
            
            profile_data = {
                "user_id": str(user_id),
                "license_number": f"PHARMA-AP-{i}",
                "license_valid_till": str(date.today() + timedelta(days=365)),
                "is_active": True
            }
            await test_client.post("/api/v1/pharmacist-profiles/", json=profile_data)
        
        response = await test_client.get("/api/v1/pharmacist-profiles/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_pharmacist_profile(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test updating a pharmacist profile."""
        # Create role, user, and profile
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        profile_data = {
            "user_id": str(user_id),
            "license_number": "PHARMA-AP-12345",
            "license_valid_till": str(date.today() + timedelta(days=365)),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/pharmacist-profiles/", json=profile_data)
        profile_id = create_resp.json()["id"]
        
        update_data = {"license_number": "PHARMA-AP-99999"}
        response = await test_client.patch(f"/api/v1/pharmacist-profiles/{profile_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["license_number"] == "PHARMA-AP-99999"
    
    async def test_delete_pharmacist_profile(
        self, 
        test_client: AsyncClient,
        sample_user_data: dict,
        sample_role_data: dict
    ):
        """Test soft deleting a pharmacist profile."""
        # Create role, user, and profile
        role_resp = await test_client.post("/api/v1/roles/", json=sample_role_data)
        role_id = role_resp.json()["id"]
        
        user_data = {**sample_user_data, "role_id": str(role_id)}
        user_resp = await test_client.post("/api/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        
        profile_data = {
            "user_id": str(user_id),
            "license_number": "PHARMA-AP-12345",
            "license_valid_till": str(date.today() + timedelta(days=365)),
            "is_active": True
        }
        create_resp = await test_client.post("/api/v1/pharmacist-profiles/", json=profile_data)
        profile_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/pharmacist-profiles/{profile_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
