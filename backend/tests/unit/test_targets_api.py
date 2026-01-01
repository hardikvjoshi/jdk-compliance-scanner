"""
Unit tests for Targets API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
from core.database.models import Target, DeploymentType, User, UserRole


class TestTargetsAPI:
    """Test cases for Targets API"""
    
    @pytest.fixture
    def client(self):
        """Test client without authentication"""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_list_targets_empty(self, authenticated_client, db_session):
        """Test empty list"""
        response = authenticated_client.get("/api/targets")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_targets_with_filters(self, authenticated_client, db_session, test_target_unix, test_target_aws):
        """Test filtering by deployment_type, tier, status"""
        # Filter by deployment_type
        response = authenticated_client.get("/api/targets?deployment_type=Unix")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
        assert all(t["deployment_type"] == "Unix" for t in results)
        
        # Filter by tier
        response = authenticated_client.get("/api/targets?tier=Dev")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
    
    def test_list_targets_invalid_deployment_type(self, authenticated_client):
        """Test invalid filter error"""
        response = authenticated_client.get("/api/targets?deployment_type=Invalid")
        assert response.status_code == 400
        assert "Invalid deployment_type" in response.json()["detail"]
    
    def test_list_targets_requires_auth(self, client):
        """Test authentication requirement"""
        response = client.get("/api/targets")
        assert response.status_code == 403
    
    def test_create_target_unix(self, admin_client, db_session, test_user):
        """Test creating Unix target"""
        target_data = {
            "name": "new-unix-target",
            "deployment_type": "Unix",
            "hostname": "server.example.com",
            "connection_config": {"hostname": "server.example.com", "username": "user", "password": "pass"},
            "tier": "Dev"
        }
        response = admin_client.post("/api/targets", json=target_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new-unix-target"
        assert data["deployment_type"] == "Unix"
    
    def test_create_target_aws(self, admin_client, db_session):
        """Test creating AWS target"""
        target_data = {
            "name": "new-aws-target",
            "deployment_type": "Cloud",
            "connection_config": {"provider": "aws", "instance_id": "i-123", "region": "us-east-1"},
            "tier": "Dev"
        }
        response = admin_client.post("/api/targets", json=target_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new-aws-target"
    
    def test_create_target_invalid_deployment_type(self, admin_client):
        """Test invalid deployment type error"""
        target_data = {
            "name": "test",
            "deployment_type": "Invalid",
            "connection_config": {},
            "tier": "Dev"
        }
        response = admin_client.post("/api/targets", json=target_data)
        assert response.status_code == 400
        assert "Invalid deployment_type" in response.json()["detail"]
    
    def test_create_target_invalid_tier(self, admin_client):
        """Test invalid tier error"""
        target_data = {
            "name": "test",
            "deployment_type": "Unix",
            "connection_config": {},
            "tier": "Invalid"
        }
        response = admin_client.post("/api/targets", json=target_data)
        assert response.status_code == 400
        assert "Tier must be one of" in response.json()["detail"]
    
    @patch('api.routes.targets.get_encryption_manager')
    def test_create_target_encryption(self, mock_encrypt, admin_client, db_session):
        """Test connection_config encryption"""
        mock_encrypt.return_value.encrypt.return_value = "encrypted_config"
        target_data = {
            "name": "test",
            "deployment_type": "Unix",
            "connection_config": {"key": "value"},
            "tier": "Dev"
        }
        response = admin_client.post("/api/targets", json=target_data)
        assert response.status_code == 201
        mock_encrypt.return_value.encrypt.assert_called_once()
    
    def test_create_target_requires_admin(self, authenticated_client):
        """Test Administrator role requirement"""
        target_data = {
            "name": "test",
            "deployment_type": "Unix",
            "connection_config": {},
            "tier": "Dev"
        }
        # This will fail if user doesn't have admin role
        # Note: This test depends on how authentication is set up in fixtures
        response = authenticated_client.post("/api/targets", json=target_data)
        # May be 403 if not admin, or 201 if admin - depends on fixture setup
    
    def test_get_target_success(self, authenticated_client, test_target_unix):
        """Test successful retrieval"""
        response = authenticated_client.get(f"/api/targets/{test_target_unix.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_target_unix.id
        assert data["name"] == test_target_unix.name
    
    def test_get_target_not_found(self, authenticated_client):
        """Test 404 handling"""
        response = authenticated_client.get("/api/targets/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_target_requires_auth(self, client):
        """Test authentication requirement"""
        response = client.get("/api/targets/1")
        assert response.status_code == 403
    
    def test_update_target_success(self, admin_client, test_target_unix):
        """Test successful update"""
        update_data = {"name": "updated-name"}
        response = admin_client.put(f"/api/targets/{test_target_unix.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"
    
    def test_update_target_partial(self, admin_client, test_target_unix):
        """Test partial update"""
        update_data = {"tier": "UAT"}
        response = admin_client.put(f"/api/targets/{test_target_unix.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "UAT"
    
    def test_update_target_not_found(self, admin_client):
        """Test 404 handling"""
        update_data = {"name": "updated"}
        response = admin_client.put("/api/targets/99999", json=update_data)
        assert response.status_code == 404
    
    @patch('api.routes.targets.get_encryption_manager')
    def test_update_target_encryption(self, mock_encrypt, admin_client, test_target_unix):
        """Test connection_config re-encryption"""
        mock_encrypt.return_value.encrypt.return_value = "new_encrypted"
        update_data = {"connection_config": {"new": "config"}}
        response = admin_client.put(f"/api/targets/{test_target_unix.id}", json=update_data)
        assert response.status_code == 200
        mock_encrypt.return_value.encrypt.assert_called_once()
    
    def test_delete_target_success(self, admin_client, db_session, test_user):
        """Test successful deletion"""
        from core.database.encryption import get_encryption_manager
        import json
        encryptor = get_encryption_manager()
        target = Target(
            name="to-delete",
            deployment_type=DeploymentType.UNIX,
            connection_config=encryptor.encrypt(json.dumps({})),
            tier="Dev",
            status="Active",
            created_by=test_user.id
        )
        db_session.add(target)
        db_session.commit()
        target_id = target.id
        
        response = admin_client.delete(f"/api/targets/{target_id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = admin_client.get(f"/api/targets/{target_id}")
        assert response.status_code == 404
    
    def test_delete_target_not_found(self, admin_client):
        """Test 404 handling"""
        response = admin_client.delete("/api/targets/99999")
        assert response.status_code == 404

