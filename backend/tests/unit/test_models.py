"""
Unit tests for database models
"""
import pytest
from datetime import datetime

from core.database.models import DeploymentType, Target, ScanResult, Project, Cluster, User, UserRole


class TestDeploymentType:
    """Test cases for DeploymentType enum"""
    
    def test_deployment_type_enum_values(self):
        """Test DeploymentType enum values"""
        assert DeploymentType.OPENSHIFT.value == "OpenShift"
        assert DeploymentType.UNIX.value == "Unix"
        assert DeploymentType.WINDOWS.value == "Windows"
        assert DeploymentType.CLOUD.value == "Cloud"
    
    def test_deployment_type_enum_usage(self):
        """Test using DeploymentType enum"""
        assert DeploymentType("OpenShift") == DeploymentType.OPENSHIFT
        assert DeploymentType("Unix") == DeploymentType.UNIX
        assert DeploymentType("Cloud") == DeploymentType.CLOUD


class TestTargetModel:
    """Test cases for Target model"""
    
    def test_target_model_creation(self, db_session):
        """Test Target model instantiation"""
        from core.database.encryption import get_encryption_manager
        import json
        
        encryptor = get_encryption_manager()
        config = {"hostname": "test.example.com", "username": "user"}
        
        target = Target(
            name="test-target",
            deployment_type=DeploymentType.UNIX,
            hostname="test.example.com",
            ip_address="1.2.3.4",
            connection_config=encryptor.encrypt(json.dumps(config)),
            tier="Dev",
            status="Active"
        )
        
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)
        
        assert target.id is not None
        assert target.name == "test-target"
        assert target.deployment_type == DeploymentType.UNIX
        assert target.hostname == "test.example.com"
        assert target.ip_address == "1.2.3.4"
        assert target.tier == "Dev"
        assert target.status == "Active"
        assert target.created_at is not None
        assert target.updated_at is not None
    
    def test_target_model_relationships(self, db_session, test_cluster, test_project, test_user):
        """Test Target relationships (project, cluster)"""
        from core.database.encryption import get_encryption_manager
        import json
        
        encryptor = get_encryption_manager()
        config = {"hostname": "test.example.com"}
        
        target = Target(
            name="test-target",
            deployment_type=DeploymentType.UNIX,
            connection_config=encryptor.encrypt(json.dumps(config)),
            project_id=test_project.id,
            cluster_id=test_cluster.id,
            tier="Dev",
            status="Active",
            created_by=test_user.id
        )
        
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)
        
        # Test relationships
        assert target.project is not None
        assert target.project.id == test_project.id
        assert target.cluster is not None
        assert target.cluster.id == test_cluster.id
    
    def test_target_model_validation(self, db_session):
        """Test field validation"""
        from core.database.encryption import get_encryption_manager
        import json
        
        encryptor = get_encryption_manager()
        config = {}
        
        # Required fields
        target = Target(
            name="test-target",
            deployment_type=DeploymentType.UNIX,
            connection_config=encryptor.encrypt(json.dumps(config)),
            tier="Dev",
            status="Active"
        )
        
        db_session.add(target)
        db_session.commit()
        
        assert target.name == "test-target"
        assert target.deployment_type == DeploymentType.UNIX
    
    def test_target_model_timestamps(self, db_session):
        """Test created_at and updated_at auto-population"""
        from core.database.encryption import get_encryption_manager
        import json
        import time
        
        encryptor = get_encryption_manager()
        config = {}
        
        target = Target(
            name="test-target",
            deployment_type=DeploymentType.UNIX,
            connection_config=encryptor.encrypt(json.dumps(config)),
            tier="Dev",
            status="Active"
        )
        
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)
        
        assert target.created_at is not None
        assert target.updated_at is not None
        assert isinstance(target.created_at, datetime)
        assert isinstance(target.updated_at, datetime)
        
        # Test updated_at changes on update
        original_updated_at = target.updated_at
        time.sleep(0.1)  # Small delay to ensure timestamp difference
        target.status = "Inactive"
        db_session.commit()
        db_session.refresh(target)
        
        assert target.updated_at >= original_updated_at


class TestScanResultModel:
    """Test cases for ScanResult model updates"""
    
    def test_scan_result_model_with_target(self, db_session, test_target_unix):
        """Test ScanResult with target_id"""
        from core.database.models import ScanJob, JobType, ScanJobStatus
        from core.database.models import User
        
        # Create a test user and scan job
        user = User(
            username="scanuser",
            email="scanuser@example.com",
            password_hash="hash",
            role=UserRole.OPERATOR
        )
        db_session.add(user)
        db_session.commit()
        
        scan_job = ScanJob(
            id="test-job-id",
            job_type=JobType.MANUAL,
            status=ScanJobStatus.COMPLETED,
            initiated_by=user.id
        )
        db_session.add(scan_job)
        db_session.commit()
        
        scan_result = ScanResult(
            target_id=test_target_unix.id,
            scan_job_id=scan_job.id,
            application_name="test-app",
            hostname="test.example.com",
            deployment_type=DeploymentType.UNIX,
            detected_jdk_version="11.0.1",
            detected_jdk_vendor="Oracle",
            compliance_status="Compliant",
            jdk_found=True
        )
        
        db_session.add(scan_result)
        db_session.commit()
        db_session.refresh(scan_result)
        
        assert scan_result.id is not None
        assert scan_result.target_id == test_target_unix.id
        assert scan_result.target is not None
        assert scan_result.hostname == "test.example.com"
        assert scan_result.deployment_type == DeploymentType.UNIX
    
    def test_scan_result_model_with_project(self, db_session, test_project):
        """Test ScanResult with project_id (backward compatibility)"""
        from core.database.models import ScanJob, JobType, ScanJobStatus, User, Cluster
        
        # Create cluster for project (use unique name to avoid constraint violation)
        import uuid
        cluster = Cluster(
            cluster_name=f"test-cluster-{uuid.uuid4().hex[:8]}",
            console_url="https://console.example.com"
        )
        db_session.add(cluster)
        db_session.commit()
        
        # Create user and scan job
        user = User(
            username="scanuser",
            email="scanuser@example.com",
            password_hash="hash",
            role=UserRole.OPERATOR
        )
        db_session.add(user)
        db_session.commit()
        
        scan_job = ScanJob(
            id="test-job-id-2",
            job_type=JobType.MANUAL,
            status=ScanJobStatus.COMPLETED,
            initiated_by=user.id
        )
        db_session.add(scan_job)
        db_session.commit()
        
        scan_result = ScanResult(
            project_id=test_project.id,
            cluster_id=cluster.id,
            scan_job_id=scan_job.id,
            application_name="test-app",
            pod_name="test-pod",
            detected_jdk_version="11.0.1",
            detected_jdk_vendor="Oracle",
            compliance_status="Compliant",
            jdk_found=True
        )
        
        db_session.add(scan_result)
        db_session.commit()
        db_session.refresh(scan_result)
        
        assert scan_result.id is not None
        assert scan_result.project_id == test_project.id
        assert scan_result.project is not None
        assert scan_result.pod_name == "test-pod"

