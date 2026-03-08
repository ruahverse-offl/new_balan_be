"""
Test suite for Medicine Compositions CRUD operations
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4


@pytest.mark.asyncio
class TestMedicineCompositionsCRUD:
    """Test all CRUD operations for Medicine Compositions."""
    
    async def test_create_medicine_composition(
        self, 
        test_client: AsyncClient, 
        sample_medicine_composition_data: dict
    ):
        """Test creating a new medicine composition."""
        response = await test_client.post("/api/v1/medicine-compositions/", json=sample_medicine_composition_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_medicine_composition_data["name"]
        assert "id" in data
        assert data["is_deleted"] is False
    
    async def test_get_medicine_composition_by_id(
        self, 
        test_client: AsyncClient,
        sample_medicine_composition_data: dict
    ):
        """Test getting a medicine composition by ID."""
        create_resp = await test_client.post("/api/v1/medicine-compositions/", json=sample_medicine_composition_data)
        comp_id = create_resp.json()["id"]
        
        response = await test_client.get(f"/api/v1/medicine-compositions/{comp_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == comp_id
    
    async def test_get_medicine_compositions_list(
        self, 
        test_client: AsyncClient,
        sample_medicine_composition_data: dict
    ):
        """Test getting list of medicine compositions."""
        for i in range(3):
            comp_data = {**sample_medicine_composition_data, "name": f"Composition_{i}"}
            await test_client.post("/api/v1/medicine-compositions/", json=comp_data)
        
        response = await test_client.get("/api/v1/medicine-compositions/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    async def test_update_medicine_composition(
        self, 
        test_client: AsyncClient,
        sample_medicine_composition_data: dict
    ):
        """Test updating a medicine composition."""
        create_resp = await test_client.post("/api/v1/medicine-compositions/", json=sample_medicine_composition_data)
        comp_id = create_resp.json()["id"]
        
        update_data = {"name": "Updated Composition"}
        response = await test_client.patch(f"/api/v1/medicine-compositions/{comp_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Composition"
    
    async def test_delete_medicine_composition(
        self, 
        test_client: AsyncClient,
        sample_medicine_composition_data: dict
    ):
        """Test soft deleting a medicine composition."""
        create_resp = await test_client.post("/api/v1/medicine-compositions/", json=sample_medicine_composition_data)
        comp_id = create_resp.json()["id"]
        
        response = await test_client.delete(f"/api/v1/medicine-compositions/{comp_id}")
        
        assert response.status_code == 200
        assert "message" in response.json()
