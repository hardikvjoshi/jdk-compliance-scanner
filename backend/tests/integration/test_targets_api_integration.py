"""
Integration tests for Targets API with real database
"""
import pytest
import json
from fastapi.testclient import TestClient

from api.main import app
from core.database.models import Target, DeploymentType
from core.database.encryption import get_encryption_manager


class TestTargetsAPIIntegration:
    """Integration tests for Targets API"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    def test_targets_api_full_crud_workflow(self, admin_client, db_session, test_user):
        """Test complete CRUD operations"""
        encryptor = get_encryption_manager()
        
        # Create
        target_data = {
            "name": "integration-test-target",
            "deployment_type": "Unix",
            "hostname": "integration.example.com",
            "connection_config": {"hostname": "integration.example.com", "username": "user"},
            "tier": "Dev"
        }
        create_response = admin_client.post("/api/targets", json=target_data)
        assert create_response.status_code == 201
        created_target = create_response.json()
        target_id = created_target["id"]
        
        # Read
        get_response = admin_client.get(f"/api/targets/{target_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "integration-test-target"
        
        # Update
        update_data = {"name": "updated-integration-target"}
        update_response = admin_client.put(f"/api/targets/{target_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "updated-integration-target"
        
        # Delete
        delete_response = admin_client.delete(f"/api/targets/{target_id}")
        assert delete_response.status_code == 204
        
        # Verify deleted
        get_response = admin_client.get(f"/api/targets/{target_id}")
        assert get_response.status_code == 404
    
    def test_targets_api_list_with_real_data(self, authenticated_client, db_session, test_target_unix, test_target_aws):
        """Test listing with real database records"""
        response = authenticated_client.get("/api/targets")
        assert response.status_code == 200
        targets = response.json()
        assert len(targets) >= 2
        assert any(t["name"] == test_target_unix.name for t in targets)
        assert any(t["name"] == test_target_aws.name for t in targets)
    
    def test_targets_api_filtering_integration(self, authenticated_client, db_session, test_target_unix):
        """Test filtering with real database queries"""
        # Filter by deployment_type
        response = authenticated_client.get("/api/targets?deployment_type=Unix")
        assert response.status_code == 200
        results = response.json()
        assert all(t["deployment_type"] == "Unix" for t in results)
        
        # Filter by tier
        response = authenticated_client.get("/api/targets?tier=Dev")
        assert response.status_code == 200
        results = response.json()
        assert all(t["tier"] == "Dev" for t in results)

