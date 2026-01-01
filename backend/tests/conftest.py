"""
Pytest fixtures and configuration for tests
"""
import pytest
import os
import sys
from typing import Generator
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database.models import Base, User, Cluster, Project, Target, DeploymentType, UserRole
from core.database.connection import get_db
from core.database.encryption import EncryptionManager
from api.main import app
from auth.middleware import get_current_user


# In-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user with Administrator role"""
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMINISTRATOR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_viewer_user(db_session: Session) -> User:
    """Create a test user with Viewer role"""
    user = User(
        username="testviewer",
        email="testviewer@example.com",
        password_hash="hashed_password",
        role=UserRole.VIEWER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_cluster(db_session: Session) -> Cluster:
    """Create a test cluster"""
    from core.database.models import Cluster
    cluster = Cluster(
        cluster_name="test-cluster",
        console_url="https://console.test-cluster.example.com",
        api_url="https://api.test-cluster.example.com",
        environment="Dev"
    )
    db_session.add(cluster)
    db_session.commit()
    db_session.refresh(cluster)
    return cluster


@pytest.fixture
def test_project(db_session: Session, test_cluster: Cluster, test_user: User) -> Project:
    """Create a test project"""
    from core.database.models import Project, ProjectStatus
    from core.database.encryption import get_encryption_manager
    
    encryptor = get_encryption_manager()
    project = Project(
        project_name="test-project",
        cluster_id=test_cluster.id,
        technology="Java",
        tribe="Test Tribe",
        tier="Dev",
        cluster_name=test_cluster.cluster_name,
        console_url="https://console.test-cluster.example.com",
        tech_read_token=encryptor.encrypt("encrypted_token"),
        tech_edit_credentials=encryptor.encrypt("encrypted_creds"),
        wrapper_cluster_token=encryptor.encrypt("encrypted_wrapper"),
        onboarded_by=test_user.id,
        status=ProjectStatus.ACTIVE
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_target_unix(db_session: Session, test_user: User) -> Target:
    """Create a test Unix target"""
    from core.database.encryption import get_encryption_manager
    import json
    
    encryptor = get_encryption_manager()
    config = {
        "hostname": "test-server.example.com",
        "username": "testuser",
        "password": "testpassword",
        "port": 22
    }
    
    target = Target(
        name="test-unix-target",
        deployment_type=DeploymentType.UNIX,
        hostname="test-server.example.com",
        ip_address="192.168.1.100",
        connection_config=encryptor.encrypt(json.dumps(config)),
        tier="Dev",
        status="Active",
        created_by=test_user.id
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


@pytest.fixture
def test_target_aws(db_session: Session, test_user: User) -> Target:
    """Create a test AWS target"""
    from core.database.encryption import get_encryption_manager
    import json
    
    encryptor = get_encryption_manager()
    config = {
        "provider": "aws",
        "instance_id": "i-1234567890abcdef0",
        "region": "us-east-1",
        "username": "ec2-user",
        "ssh_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
    }
    
    target = Target(
        name="test-aws-target",
        deployment_type=DeploymentType.CLOUD,
        hostname="ec2-1-2-3-4.compute-1.amazonaws.com",
        ip_address="1.2.3.4",
        connection_config=encryptor.encrypt(json.dumps(config)),
        tier="Dev",
        status="Active",
        created_by=test_user.id
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


@pytest.fixture
def mock_encryption_manager():
    """Mock encryption manager"""
    mock_manager = Mock(spec=EncryptionManager)
    mock_manager.encrypt = Mock(side_effect=lambda x: f"encrypted_{x}")
    mock_manager.decrypt = Mock(side_effect=lambda x: x.replace("encrypted_", "") if x.startswith("encrypted_") else x)
    return mock_manager


@pytest.fixture
def mock_ssh_client():
    """Mock paramiko SSH client"""
    mock_client = MagicMock()
    mock_client.exec_command.return_value = (
        MagicMock(read=lambda: b"stdout output"),
        MagicMock(read=lambda: b"stderr output"),
        MagicMock(channel=MagicMock(recv_exit_status=lambda: 0))
    )
    mock_client.close = Mock()
    return mock_client


@pytest.fixture
def authenticated_client(db_session: Session, test_user: User) -> TestClient:
    """FastAPI TestClient with authentication"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    async def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db_session: Session, test_user: User) -> TestClient:
    """FastAPI TestClient with admin authentication"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    async def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client using moto"""
    try:
        from moto import mock_ec2
        return mock_ec2()
    except ImportError:
        # If moto not available, return a simple mock
        return MagicMock()


@pytest.fixture
def mock_azure_client():
    """Mock Azure client"""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_gcp_client():
    """Mock GCP client"""
    mock_client = MagicMock()
    return mock_client

