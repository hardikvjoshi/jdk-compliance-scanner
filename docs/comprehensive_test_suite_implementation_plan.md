---
name: Add Comprehensive Test Suite
overview: Add comprehensive unit and integration tests for all newly implemented features including Unix scanner, Cloud scanners (AWS/Azure/GCP), Targets API, database models, and ScannerFactory using pytest.
todos: []
---

# Add

Comprehensive Test Suite for Unix/Cloud Scanner Implementation

## Overview

Create comprehensive test coverage for all newly implemented features using pytest. Tests will include both unit tests (with mocked dependencies) and integration tests (with mocked connections) for scanners, API endpoints, and database models.

## Testing Framework Setup

### Phase 1: Test Infrastructure Setup

#### 1.1 Create Test Directory Structure

**New Directory**: `backend/tests/`

```javascript
backend/tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_unix_scanner.py
│   ├── test_aws_scanner.py
│   ├── test_azure_scanner.py
│   ├── test_gcp_scanner.py
│   ├── test_cloud_scanner.py
│   ├── test_factory.py
│   ├── test_targets_api.py
│   └── test_models.py
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_scanner_integration.py
│   └── test_targets_api_integration.py
└── fixtures/                      # Test fixtures and utilities
    ├── __init__.py
    ├── mock_scanner.py
    └── db_fixtures.py
```



#### 1.2 Update requirements.txt

Add testing dependencies to `backend/requirements.txt`:

```python
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
httpx>=0.24.1  # For FastAPI test client
# Mocking cloud services
moto>=4.2.0  # AWS mocking
responses>=0.23.1  # HTTP mocking
```



#### 1.3 Create pytest Configuration

**New File**: `backend/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=core
    --cov=api
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
asyncio_mode = auto
```



## Unit Tests

### Phase 2: Scanner Unit Tests

#### 2.1 Unix Scanner Tests (`backend/tests/unit/test_unix_scanner.py`)

Test the Unix scanner with mocked paramiko:

**Test Cases**:

- `test_unix_scanner_init` - Test initialization with various configs

- `test_unix_scanner_connect_with_password` - Test SSH connection with password auth

- `test_unix_scanner_connect_with_key` - Test SSH connection with RSA key

- `test_unix_scanner_connect_with_ecdsa_key` - Test SSH connection with ECDSA key

- `test_unix_scanner_connect_with_ed25519_key` - Test SSH connection with Ed25519 key

- `test_unix_scanner_connect_auth_failure` - Test authentication failure handling

- `test_unix_scanner_connect_connection_error` - Test connection error handling

- `test_unix_scanner_disconnect` - Test disconnect functionality

- `test_unix_scanner_execute_command_success` - Test successful command execution

- `test_unix_scanner_execute_command_failure` - Test command execution failure

- `test_unix_scanner_execute_command_not_connected` - Test execution when not connected

- `test_unix_scanner_decrypt_credentials` - Test credential decryption

- `test_unix_scanner_scan_method` - Test full scan workflow

- `test_unix_scanner_timeout_handling` - Test timeout scenarios

**Mocking Strategy**:

- Mock `paramiko.SSHClient` and its methods

- Mock `paramiko.RSAKey`, `paramiko.ECDSAKey`, `paramiko.Ed25519Key`

- Mock encryption manager for credential handling

#### 2.2 AWS Scanner Tests (`backend/tests/unit/test_aws_scanner.py`)

Test AWS scanner with mocked boto3:

**Test Cases**:

- `test_aws_scanner_init` - Test initialization

- `test_aws_scanner_get_aws_client_with_credentials` - Test boto3 client creation with credentials

- `test_aws_scanner_get_aws_client_default_credentials` - Test default credentials

- `test_aws_scanner_get_instance_ip` - Test EC2 IP retrieval (public and private)

- `test_aws_scanner_get_instance_ip_not_found` - Test instance not found handling

- `test_aws_scanner_connect_success` - Test successful SSH connection

- `test_aws_scanner_connect_failure` - Test connection failure

- `test_aws_scanner_execute_command` - Test command execution

- `test_aws_scanner_disconnect` - Test disconnect

- `test_aws_scanner_scan_method` - Test full scan workflow

**Mocking Strategy**:

- Use `moto` library to mock AWS services (EC2)

- Mock `paramiko.SSHClient` for SSH operations

- Mock encryption manager

#### 2.3 Azure Scanner Tests (`backend/tests/unit/test_azure_scanner.py`)

Test Azure scanner with mocked Azure SDK:

**Test Cases**:

- `test_azure_scanner_init` - Test initialization

- `test_azure_scanner_get_azure_credentials_service_principal` - Test service principal auth

- `test_azure_scanner_get_azure_credentials_default` - Test default credentials

- `test_azure_scanner_get_vm_ip` - Test VM IP retrieval

- `test_azure_scanner_connect_success` - Test successful connection

- `test_azure_scanner_connect_failure` - Test connection failure

- `test_azure_scanner_execute_command` - Test command execution

- `test_azure_scanner_disconnect` - Test disconnect

- `test_azure_scanner_missing_sdk` - Test ImportError handling when SDK not available

**Mocking Strategy**:

- Mock Azure SDK classes (`DefaultAzureCredential`, `ClientSecretCredential`, `NetworkManagementClient`)

- Mock `paramiko.SSHClient` for SSH operations

- Mock encryption manager

#### 2.4 GCP Scanner Tests (`backend/tests/unit/test_gcp_scanner.py`)

Test GCP scanner with mocked GCP SDK:

**Test Cases**:

- `test_gcp_scanner_init` - Test initialization

- `test_gcp_scanner_get_gcp_client_with_service_account` - Test service account auth

- `test_gcp_scanner_get_gcp_client_default` - Test default credentials

- `test_gcp_scanner_get_instance_ip_external` - Test external IP retrieval

- `test_gcp_scanner_get_instance_ip_internal` - Test internal IP fallback

- `test_gcp_scanner_connect_success` - Test successful connection

- `test_gcp_scanner_connect_failure` - Test connection failure

- `test_gcp_scanner_execute_command` - Test command execution

- `test_gcp_scanner_disconnect` - Test disconnect

- `test_gcp_scanner_missing_sdk` - Test ImportError handling when SDK not available

**Mocking Strategy**:

- Mock GCP SDK classes (`compute_v1.InstancesClient`, `service_account.Credentials`)

- Mock `paramiko.SSHClient` for SSH operations

- Mock encryption manager

#### 2.5 Cloud Scanner Tests (`backend/tests/unit/test_cloud_scanner.py`)

Test the CloudScanner routing class:

**Test Cases**:

- `test_cloud_scanner_aws_routing` - Test routing to AWS scanner

- `test_cloud_scanner_azure_routing` - Test routing to Azure scanner

- `test_cloud_scanner_gcp_routing` - Test routing to GCP scanner

- `test_cloud_scanner_unsupported_provider` - Test unsupported provider error

- `test_cloud_scanner_missing_aws_sdk` - Test AWS SDK missing error

- `test_cloud_scanner_missing_azure_sdk` - Test Azure SDK missing error

- `test_cloud_scanner_missing_gcp_sdk` - Test GCP SDK missing error

- `test_cloud_scanner_delegate_methods` - Test method delegation (connect, disconnect, execute_command, scan)

#### 2.6 Scanner Factory Tests (`backend/tests/unit/test_factory.py`)

Test ScannerFactory registration and creation:

**Test Cases**:

- `test_factory_register_scanner` - Test scanner registration

- `test_factory_create_scanner_openshift` - Test OpenShift scanner creation

- `test_factory_create_scanner_unix` - Test Unix scanner creation

- `test_factory_create_scanner_aws` - Test AWS scanner creation

- `test_factory_create_scanner_azure` - Test Azure scanner creation

- `test_factory_create_scanner_gcp` - Test GCP scanner creation

- `test_factory_create_scanner_cloud` - Test Cloud scanner creation (routing)

- `test_factory_create_scanner_not_registered` - Test unregistered scanner error

- `test_factory_case_insensitive` - Test case-insensitive deployment type matching

### Phase 3: API Unit Tests

#### 3.1 Targets API Tests (`backend/tests/unit/test_targets_api.py`)

Test Targets API endpoints with mocked database:

**Test Cases for GET /api/targets**:

- `test_list_targets_empty` - Test empty list

- `test_list_targets_with_filters` - Test filtering by deployment_type, tier, status

- `test_list_targets_invalid_deployment_type` - Test invalid filter error

- `test_list_targets_requires_auth` - Test authentication requirement

**Test Cases for POST /api/targets**:

- `test_create_target_unix` - Test creating Unix target

- `test_create_target_aws` - Test creating AWS target

- `test_create_target_azure` - Test creating Azure target

- `test_create_target_gcp` - Test creating GCP target

- `test_create_target_invalid_deployment_type` - Test invalid deployment type error

- `test_create_target_invalid_tier` - Test invalid tier error

- `test_create_target_encryption` - Test connection_config encryption

- `test_create_target_requires_admin` - Test Administrator role requirement

**Test Cases for GET /api/targets/{id}`:

- `test_get_target_success` - Test successful retrieval

- `test_get_target_not_found` - Test 404 handling

- `test_get_target_requires_auth` - Test authentication requirement

**Test Cases for PUT /api/targets/{id}`:

- `test_update_target_success` - Test successful update

- `test_update_target_partial` - Test partial update

- `test_update_target_not_found` - Test 404 handling

- `test_update_target_requires_admin` - Test Administrator role requirement

- `test_update_target_encryption` - Test connection_config re-encryption

**Test Cases for DELETE /api/targets/{id}`:

- `test_delete_target_success` - Test successful deletion

- `test_delete_target_not_found` - Test 404 handling

- `test_delete_target_requires_admin` - Test Administrator role requirement

**Mocking Strategy**:

- Use FastAPI TestClient for API endpoint testing

- Mock database session using pytest fixtures

- Mock authentication middleware

- Mock encryption manager

### Phase 4: Database Model Tests

#### 4.1 Database Models Tests (`backend/tests/unit/test_models.py`)

Test database models and enums:

**Test Cases**:

- `test_deployment_type_enum_values` - Test DeploymentType enum values

- `test_target_model_creation` - Test Target model instantiation

- `test_target_model_relationships` - Test Target relationships (project, cluster)

- `test_scan_result_model_with_target` - Test ScanResult with target_id

- `test_scan_result_model_with_project` - Test ScanResult with project_id (backward compatibility)

- `test_target_model_validation` - Test field validation

- `test_target_model_timestamps` - Test created_at and updated_at auto-population

## Integration Tests

### Phase 5: Integration Tests

#### 5.1 Scanner Integration Tests (`backend/tests/integration/test_scanner_integration.py`)

Test scanners with mocked but realistic connections:

**Test Cases**:

- `test_unix_scanner_full_workflow` - Test complete Unix scan workflow with mocked SSH

- `test_aws_scanner_full_workflow` - Test complete AWS scan workflow with mocked EC2 and SSH

- `test_azure_scanner_full_workflow` - Test complete Azure scan workflow (if SDK available)

- `test_gcp_scanner_full_workflow` - Test complete GCP scan workflow (if SDK available)

- `test_factory_scanner_creation_integration` - Test factory creates correct scanner types

- `test_parallel_executor_with_unix_scanners` - Test parallel execution with Unix scanners

- `test_parallel_executor_with_cloud_scanners` - Test parallel execution with Cloud scanners

#### 5.2 Targets API Integration Tests (`backend/tests/integration/test_targets_api_integration.py`)

Test API endpoints with real database (in-memory SQLite):

**Test Cases**:

- `test_targets_api_full_crud_workflow` - Test complete CRUD operations

- `test_targets_api_list_with_real_data` - Test listing with real database records

- `test_targets_api_filtering_integration` - Test filtering with real database queries

- `test_targets_api_authentication_flow` - Test authentication integration

## Test Fixtures and Utilities

### Phase 6: Test Infrastructure

#### 6.1 Pytest Fixtures (`backend/tests/conftest.py`)

Create reusable fixtures:

**Fixtures**:

- `db_session` - Database session fixture (in-memory SQLite)

- `test_user` - Test user fixture (Administrator role)

- `test_viewer_user` - Test viewer user fixture

- `test_cluster` - Test cluster fixture

- `test_project` - Test project fixture

- `test_target_unix` - Test Unix target fixture

- `test_target_aws` - Test AWS target fixture

- `authenticated_client` - FastAPI TestClient with authentication

- `admin_client` - FastAPI TestClient with admin authentication

- `mock_ssh_client` - Mocked paramiko.SSHClient fixture

- `mock_encryption_manager` - Mocked encryption manager fixture

- `mock_boto3_client` - Mocked boto3 client fixture (using moto)

- `mock_azure_client` - Mocked Azure client fixture

- `mock_gcp_client` - Mocked GCP client fixture

#### 6.2 Test Utilities (`backend/tests/fixtures/`)

Helper modules for test setup:**Files**:

- `mock_scanner.py` - Mock scanner implementations for testing

- `db_fixtures.py` - Database setup/teardown utilities

## Test Execution

### Phase 7: Test Configuration

#### 7.1 Add Test Scripts

Update or create test execution scripts:

**Option 1**: Add to `backend/README.md`:

````markdown
## Testing

Run tests:
```bash
# With virtual environment activated
pytest                    # Run all tests
pytest tests/unit/        # Run only unit tests
pytest tests/integration/ # Run only integration tests
pytest --cov              # Run with coverage
````
````javascript

**Option 2**: Create `backend/run_tests.sh`:

```bash
#!/bin/bash
source .venv/bin/activate
pytest -v --cov=core --cov=api --cov-report=term-missing --cov-report=html
````



## Testing Strategy Summary

### Unit Tests Coverage

- **Scanners**: All scanner classes (Unix, AWS, Azure, GCP, Cloud routing)

- Connection logic

- Command execution

- Error handling

- Credential decryption

- Provider-specific logic

- **API Endpoints**: Targets API

- All CRUD operations

- Authentication and authorization

- Input validation

- Error responses

- **Database Models**: New models and enums

- DeploymentType enum

- Target model

- ScanResult model updates

- **Factory**: ScannerFactory

- Registration

- Scanner creation

- Error handling

### Integration Tests Coverage

- Scanner workflows with mocked connections

- API endpoints with real database

- Factory integration with all scanner types

- Parallel executor with different scanner types

### Mocking Strategy

- **SSH**: Mock paramiko.SSHClient

- **AWS**: Use moto library for boto3 mocking

- **Azure**: Mock Azure SDK classes

- **GCP**: Mock GCP SDK classes

- **Database**: Use in-memory SQLite for integration tests

- **Authentication**: Mock JWT tokens and user sessions

- **Encryption**: Mock encryption manager for unit tests

## Files to Create

1. `backend/tests/__init__.py`

2. `backend/tests/conftest.py`

3. `backend/tests/unit/__init__.py`

4. `backend/tests/unit/test_unix_scanner.py`

5. `backend/tests/unit/test_aws_scanner.py`

6. `backend/tests/unit/test_azure_scanner.py`

7. `backend/tests/unit/test_gcp_scanner.py`

8. `backend/tests/unit/test_cloud_scanner.py`

9. `backend/tests/unit/test_factory.py`

10. `backend/tests/unit/test_targets_api.py`

11. `backend/tests/unit/test_models.py`

12. `backend/tests/integration/__init__.py`

13. `backend/tests/integration/test_scanner_integration.py`

14. `backend/tests/integration/test_targets_api_integration.py`

15. `backend/tests/fixtures/__init__.py`

16. `backend/tests/fixtures/mock_scanner.py`

17. `backend/tests/fixtures/db_fixtures.py`

18. `backend/pytest.ini`

## Files to Update

1. `backend/requirements.txt` - Add testing dependencies

2. `backend/README.md` - Add testing section

## Notes

- All tests use pytest fixtures for setup/teardown

- Unit tests mock external dependencies (SSH, cloud SDKs, database)

- Integration tests use real database (in-memory SQLite) and mocked external services

- Test coverage goal: >80% for new implementations

- Tests follow AAA pattern (Arrange, Act, Assert)