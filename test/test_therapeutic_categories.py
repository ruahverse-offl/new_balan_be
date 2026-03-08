"""
Test suite for Therapeutic Categories CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestTherapeuticCategoriesCRUD:
    """Test all CRUD operations for Therapeutic Categories."""
    
    async def test_create_therapeutic_category(
        self, 
        test_client: AsyncClient, 
        sample_therapeutic_category_data: dict
    ):
        """Test creating a new therapeutic category."""
        response = await test_client.post("/api/v1/therapeutic-categories/", json=sample_therapeutic_category_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_therapeutic_category_data["name"]
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_therapeutic_category_by_id(
        self, 
        test_client: AsyncClient,
        sample_therapeutic_category_data: dict
    ):
        """Test getting a therapeutic category by ID."""
        create_resp = await test_client.post("/api/v1/therapeutic-categories/", json=sample_therapeutic_category_data)
        cat_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/therapeutic-categories/{cat_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cat_id
    
    async def test_get_therapeutic_categories_list(
        self, 
        test_client: AsyncClient,
        sample_therapeutic_category_data: dict
    ):
        """Test getting list of therapeutic categories."""
        for i in range(3):
            cat_data = {**sample_therapeutic_category_data, "name": f"Category_{i}"}
            await test_client.post("/api/v1/therapeutic-categories/", json=cat_data)
        
        response = await test_client.get("/api/v1/therapeutic-categories/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_therapeutic_category(
        self, 
        test_client: AsyncClient,
        sample_therapeutic_category_data: dict
    ):
        """Test updating a therapeutic category."""
        create_resp = await test_client.post("/api/v1/therapeutic-categories/", json=sample_therapeutic_category_data)
        cat_id = create_resp.json()["id"]
        
        update_data = {"name": "Updated Category"}
        response = await test_client.patch(f"/api/v1/therapeutic-categories/{cat_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
    
    async def test_delete_therapeutic_category(
        self, 
        test_client: AsyncClient,
        sample_therapeutic_category_data: dict
    ):
        """Test soft deleting a therapeutic category."""
        create_resp = await test_client.post("/api/v1/therapeutic-categories/", json=sample_therapeutic_category_data)
        cat_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/therapeutic-categories/{cat_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
