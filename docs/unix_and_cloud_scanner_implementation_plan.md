---
name: Add Unix and Cloud Scanner Support
overview: Extend the scanner architecture to support Unix/Linux systems (SSH-based) and Cloud systems (AWS, Azure, GCP). The architecture already supports extensibility via BaseScanner and ScannerFactory, so we'll implement UnixScanner and CloudScanner following the same patterns as OpenShiftScanner.
todos: []
---

# Add Unix/Linux and Cloud Scanner Support

## Overview

Currently, only OpenShift scanner is implemented. This plan adds Unix/Linux scanner (SSH-based) and Cloud scanner (AWS, Azure, GCP) support while maintaining the existing extensible architecture.

## Current State

- ✅ BaseScanner abstract class (extensible foundation)
- ✅ ScannerFactory pattern (allows adding scanners without modifying core)
- ✅ OpenShiftScanner implementation
- ✅ Shared JDK detection (works for all scanner types)
- ✅ Parallel executor (scanner-agnostic)

## Implementation Plan

### Phase 1: Database Schema Updates

#### 1.1 Add Deployment Type Support

**File**: `backend/core/database/models.py`Add `deployment_type` field to support multiple deployment types:

- Add `deployment_type` enum: OpenShift, Unix, Windows, Cloud
- Add `deployment_type` field to `projects` table (for backward compatibility with OpenShift)
- OR create separate `targets` table for non-OpenShift systems

**Decision**: Create a unified `targets` table that can store:

- OpenShift projects (existing)
- Unix/Linux hosts
- Cloud instances (EC2, VMs, containers)

**New Table**: `targets`

- `id` (Primary Key)
- `name` (String) - Target name/hostname
- `deployment_type` (Enum: OpenShift, Unix, Cloud, Windows)
- `hostname` (String, nullable) - For Unix systems
- `ip_address` (String, nullable)
- `connection_config` (JSON/Text) - Connection details (encrypted)
- `project_id` (Foreign Key, nullable) - For OpenShift projects
- `cluster_id` (Foreign Key, nullable)
- `tier` (String) - Dev, UAT, Production
- `status` (String) - Active, Inactive
- `created_at`, `updated_at`

### Phase 2: Unix/Linux Scanner Implementation

#### 2.1 Unix Scanner (`backend/core/scanner/unix_scanner.py`)

Extend `BaseScanner` for Unix/Linux systems using SSH.**Key Features**:

- SSH connection using paramiko library
- Execute commands via SSH
- Support for SSH key-based and password authentication
- Handle different Unix variants (Linux, Solaris, AIX, etc.)
- Connection pooling for efficiency

**Configuration**:

```python
{
    "hostname": "server.example.com",
    "port": 22,
    "username": "user",
    "password": "encrypted_password",  # or None
    "ssh_key": "encrypted_private_key",  # or None
    "ssh_key_passphrase": "encrypted_passphrase",  # or None
    "timeout": 30
}
```

**Methods to Implement**:

- `connect()` - Establish SSH connection
- `disconnect()` - Close SSH connection
- `execute_command()` - Execute command via SSH

#### 2.2 Register Unix Scanner

**File**: `backend/core/scanner/factory.py`Add Unix scanner registration:

```python
from core.scanner.unix_scanner import UnixScanner
ScannerFactory.register_scanner("unix", UnixScanner)
```



### Phase 3: Cloud Scanner Implementation

#### 3.1 Cloud Scanner Base (`backend/core/scanner/cloud_scanner.py`)

Create base CloudScanner class that handles common cloud operations.**Supported Clouds**:

- AWS (EC2, ECS, Lambda)
- Azure (VMs, Container Instances)
- GCP (Compute Engine, GKE)

**Configuration Structure**:

```python
{
    "provider": "aws|azure|gcp",
    "credentials": {
        # Provider-specific credentials (encrypted)
    },
    "region": "us-east-1",
    "instance_id": "i-1234567890abcdef0",  # For specific instance
    "resource_group": "rg-name",  # Azure
    "project_id": "gcp-project-id"  # GCP
}
```



#### 3.2 AWS Scanner (`backend/core/scanner/cloud/aws_scanner.py`)

**Features**:

- Connect via AWS SDK (boto3)
- EC2 instances: SSH via Session Manager or direct SSH
- ECS containers: Execute commands in containers
- Lambda: Check runtime versions
- IAM role or access key authentication

#### 3.3 Azure Scanner (`backend/core/scanner/cloud/azure_scanner.py`)

**Features**:

- Connect via Azure SDK (azure-identity, azure-mgmt-compute)
- VMs: SSH or Run Command
- Container Instances: Execute commands
- Service Principal or Managed Identity authentication

#### 3.4 GCP Scanner (`backend/core/scanner/cloud/gcp_scanner.py`)

**Features**:

- Connect via GCP SDK (google-cloud-compute)
- Compute Engine VMs: SSH
- GKE clusters: Similar to OpenShift
- Service Account authentication

#### 3.5 Cloud Scanner Factory (`backend/core/scanner/cloud_scanner.py`)

Unified interface that routes to provider-specific scanners:

```python
class CloudScanner(BaseScanner):
    def __init__(self, config):
        provider = config.get("provider")
        if provider == "aws":
            self.scanner = AWSScanner(config)
        elif provider == "azure":
            self.scanner = AzureScanner(config)
        elif provider == "gcp":
            self.scanner = GCPScanner(config)
```

**Alternative Approach**: Register each cloud provider separately:

- `ScannerFactory.register_scanner("aws", AWSScanner)`
- `ScannerFactory.register_scanner("azure", AzureScanner)`
- `ScannerFactory.register_scanner("gcp", GCPScanner)`

### Phase 4: API Updates

#### 4.1 Update Projects API

**File**: `backend/api/routes/projects.py`Add support for deployment_type when creating projects:

- OpenShift projects (existing functionality)
- Unix targets
- Cloud targets

#### 4.2 Create Targets API

**New File**: `backend/api/routes/targets.py`REST endpoints for managing scan targets:

- `GET /api/targets` - List all targets (with filters)
- `POST /api/targets` - Create new target (Unix/Cloud)
- `GET /api/targets/{id}` - Get target details
- `PUT /api/targets/{id}` - Update target
- `DELETE /api/targets/{id}` - Delete target

#### 4.3 Update Scan API

**File**: `backend/api/routes/scans.py` (to be created)Scan endpoints that work with any deployment type:

- `POST /api/scans` - Trigger scan (supports OpenShift, Unix, Cloud)
- `GET /api/scans` - List scan jobs
- `GET /api/scans/{id}` - Get scan results
- `GET /api/scans/{id}/results` - Get detailed results

### Phase 5: Dependencies

Update `backend/requirements.txt`:

- `paramiko>=3.0.0` - SSH client for Unix
- `boto3>=1.28.0` - AWS SDK
- `azure-identity>=1.15.0` - Azure authentication
- `azure-mgmt-compute>=30.0.0` - Azure compute
- `google-cloud-compute>=1.14.0` - GCP compute
- `cryptography>=41.0.7` - Already included, needed for SSH

### Phase 6: Documentation Updates

Update:

- `backend/README.md` - Add Unix and Cloud scanner info
- Architecture diagrams
- API documentation

## Architecture Benefits

The existing architecture already supports this extensibility:

1. **BaseScanner**: All scanners extend this - no core changes needed
2. **ScannerFactory**: New scanners register themselves - follows Open/Closed Principle
3. **JDK Detection**: Shared component works for all scanner types
4. **Parallel Executor**: Works with any BaseScanner implementation
5. **Error Handler**: Centralized logging works for all scanners

## File Structure

```javascript
backend/core/scanner/
├── base.py                    # Abstract BaseScanner (no changes)
├── factory.py                 # Add Unix/Cloud registrations
├── openshift_scanner.py       # Existing (no changes)
├── unix_scanner.py            # NEW - SSH-based scanner
├── cloud_scanner.py           # NEW - Cloud scanner base/routing
├── cloud/
│   ├── __init__.py
│   ├── aws_scanner.py         # NEW - AWS implementation
│   ├── azure_scanner.py       # NEW - Azure implementation
│   └── gcp_scanner.py         # NEW - GCP implementation
├── parallel_executor.py       # No changes (scanner-agnostic)
├── error_handler.py           # No changes (works for all)
└── connection_manager.py      # No changes
```



## Implementation Order

1. Unix Scanner (simpler, SSH is well-established)
2. Cloud Scanner - AWS (most common)
3. Cloud Scanner - Azure
4. Cloud Scanner - GCP
5. API updates to support new target types
6. Database schema updates (if needed)

## Testing Strategy

- Unit tests for each scanner type
- Integration tests with mock SSH/cloud connections
- Test with real systems (optional, for validation)

## Notes

- All credentials stored encrypted
- All credentials st (same as OpenShift tokens)
- Connection pooling for efficiency
- Timeout handling for all connection types