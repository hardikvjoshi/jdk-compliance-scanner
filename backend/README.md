# JDK Compliance Scanner - Backend API

REST API backend for JDK compliance checking across OpenShift clusters.

**Runs without Docker** - This application is designed to run directly on your local machine or server without requiring Docker. Simply install Python dependencies and run!

## Features

- **Authentication**: JWT-based authentication with role-based access control (Administrator, Viewer, Operator)
- **Database**: SQLite file-based database with encryption support
- **Cluster Management**: Manage OpenShift clusters (Dev/UAT/Production)
- **Project Onboarding**: Administrator API for onboarding projects with required credentials
- **JDK Detection**: Shared JDK version detection engine supporting multiple vendors
- **Scanner Architecture**: Extensible scanner framework following SOLID principles
- **Multiple Deployment Type Support**:
  - **OpenShift Scanner**: Scans pods in OpenShift/Kubernetes namespaces
  - **Unix/Linux Scanner**: Scans remote Unix/Linux systems via SSH
  - **Cloud Scanners**: AWS EC2, Azure VMs, and GCP Compute Engine support
- **Compliance Checking**: Validates JDK versions against database
- **Exemption Management**: Manage application exemptions (API pending)
- **Parallel Scanning**: Configurable thread pool for parallel scanning

## Project Structure

```
backend/
├── api/                    # API routes and main application
│   ├── routes/            # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── clusters.py   # Cluster management
│   │   ├── projects.py   # Project onboarding
│   │   └── jdk.py        # JDK versions management
│   └── main.py           # FastAPI application
├── auth/                  # Authentication module
│   ├── authenticator.py  # JWT token generation/validation
│   └── middleware.py     # Authentication middleware
├── core/                  # Core services
│   ├── database/         # Database models and connection
│   ├── scanner/          # Scanner architecture
│   └── compliance/       # Compliance checking
├── config/               # Configuration management
├── scripts/              # Utility scripts
└── requirements.txt      # Python dependencies
```

## Quick Start (Without Docker)

The application runs directly on your machine - no Docker required!

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create and configure environment file
cp env.example .env
# Edit .env with your settings (at minimum, set a secure JWT_SECRET_KEY)

# 5. Initialize database
python scripts/init_db.py

# 6. Run the server
python run.py
```

The API will be available at `http://localhost:8000` with Swagger docs at `/docs`

**Note**: Remember to activate the virtual environment (`.venv`) before running commands. Use `deactivate` to exit the virtual environment when done.

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (usually included with Python)

**No Docker required!** The application uses SQLite file-based database, so no external database server is needed.

### 1. Create Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# With virtual environment activated
pip install -r requirements.txt
```

Alternatively, install as a package (recommended for development):
```bash
# With virtual environment activated
pip install -e .
```

### 3. Configure Environment

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

**Note**: Ensure you're running commands from the `backend/` directory, as all imports are relative to the backend folder.

Edit `.env` with your settings:
- `DB_PATH`: Path to SQLite database file
- `DB_PASSWORD`: Database password (optional for now)
- `JWT_SECRET_KEY`: Secret key for JWT tokens (change in production!)
- `ENCRYPTION_PASSWORD`: Password for credential encryption
- `ADMIN_PASSWORD`: Initial admin user password

### 4. Initialize Database

```bash
# With virtual environment activated
python scripts/init_db.py
```

This will:
- Create the database file
- Create all tables
- Create default admin user (username: `admin`, password: from `ADMIN_PASSWORD` env var)

### 5. Run the Server

**Option 1: Using the run script (recommended)**
```bash
python run.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using the quick start script**
```bash
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat
```

The quick start scripts automatically:
- Create `.venv` virtual environment if it doesn't exist
- Activate the virtual environment
- Install dependencies
- Initialize database if needed
- Start the server

The API will be available at `http://localhost:8000`

**Note**: The application runs entirely without Docker. It uses:
- SQLite file-based database (no external database server needed)
- Python virtual environment (`.venv` - automatically created by startup scripts)
- Local file storage for data

**Virtual Environment**: All commands assume the `.venv` virtual environment is activated. Use `deactivate` to exit the virtual environment when done.

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/validate` - Validate current token
- `POST /api/auth/logout` - Logout (token invalidation)

### Clusters (Administrator only for create/update/delete)
- `GET /api/clusters` - List all clusters
- `POST /api/clusters` - Create new cluster
- `GET /api/clusters/{id}` - Get cluster details
- `PUT /api/clusters/{id}` - Update cluster
- `DELETE /api/clusters/{id}` - Delete cluster

### Projects (Administrator only)
- `GET /api/projects` - List projects (with filters)
- `POST /api/projects` - Onboard new project (all fields required)
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `PUT /api/projects/{id}/credentials` - Update credentials
- `DELETE /api/projects/{id}` - Retire project
- `POST /api/projects/{id}/activate` - Reactivate project
- `GET /api/projects/{id}/validation` - Validate project

### Targets (Administrator only for create/update/delete)
- `GET /api/targets` - List all targets (Unix/Cloud) with filters
- `POST /api/targets` - Create new target (Unix/Cloud)
- `GET /api/targets/{id}` - Get target details
- `PUT /api/targets/{id}` - Update target
- `DELETE /api/targets/{id}` - Delete target

### JDK Versions (Administrator only for create/update)
- `GET /api/jdk-versions` - List JDK versions
- `POST /api/jdk-versions` - Add JDK version
- `GET /api/jdk-versions/{id}` - Get JDK version
- `PUT /api/jdk-versions/{id}` - Update JDK version
- `PUT /api/jdk-versions/{id}/compliance-status` - Update compliance status

## Authentication

Most endpoints require JWT authentication. After login, include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Project Onboarding

Before a project can be scanned, it must be onboarded by an Administrator with all required fields:

1. **project_name**: Project/namespace name in OpenShift
2. **cluster_id**: Reference to cluster
3. **technology**: Technology stack (Java, Python, Node, Go, Mixed)
4. **tribe**: Organizational tribe/team
5. **tier**: Environment tier (Dev, UAT, Production)
6. **cluster_name**: Cluster name
7. **console_url**: OpenShift console URL
8. **tech_read_token**: Encrypted read-only token
9. **tech_edit_credentials**: Encrypted edit credentials
10. **wrapper_cluster_token**: Encrypted wrapper cluster token

All credentials are encrypted at rest using application-level encryption.

## Running Without Docker

This application **runs without Docker**. See [RUNNING_WITHOUT_DOCKER.md](RUNNING_WITHOUT_DOCKER.md) for detailed instructions.

**Quick Start:**
```bash
cd backend
pip install -r requirements.txt
cp env.example .env
python scripts/init_db.py
python run.py
```

## Status

This is a work in progress. The following features are implemented:

✅ Database schema and models
✅ Database connection (SQLite)
✅ Credential encryption
✅ Authentication (JWT)
✅ Cluster management API
✅ Project onboarding API
✅ JDK versions management API
✅ Scanner architecture (BaseScanner, Factory)
✅ OpenShift Scanner implementation
✅ Unix/Linux Scanner implementation (SSH-based)
✅ Cloud Scanner implementations (AWS, Azure, GCP)
✅ Targets API for managing Unix/Cloud scan targets
✅ JDK detection engine
✅ Compliance checker
✅ Parallel executor

🔄 In Progress:
- Scanning API endpoints
- Exemption management API
- Scaling manager
- Reporting engine
- Docker setup

## Development

### Scanner Architecture

The JDK Compliance Scanner uses an extensible architecture based on the Strategy and Factory patterns:

#### Supported Deployment Types

1. **OpenShift/Kubernetes**: Scans pods in OpenShift namespaces
2. **Unix/Linux**: Scans remote Unix/Linux systems via SSH
3. **Cloud Platforms**:
   - **AWS**: EC2 instances via SSH
   - **Azure**: Virtual Machines via SSH  
   - **GCP**: Compute Engine VMs via SSH

#### Architecture Components

- **BaseScanner**: Abstract base class defining the scanner interface
- **ScannerFactory**: Factory pattern for creating scanner instances based on deployment type
- **Scanner Implementations**: Concrete scanners for each deployment type
- **ParallelExecutor**: Scanner-agnostic parallel execution engine
- **JDKDetector**: Shared JDK version detection logic

#### Adding New Scanner Types

To add support for a new deployment type:

1. Create a new scanner class extending `BaseScanner`
2. Implement required methods: `connect()`, `disconnect()`, `execute_command()`
3. Register the scanner in `ScannerFactory` using `register_scanner()`
4. The scanner will automatically work with the parallel executor and JDK detection engine

See `backend/core/scanner/` for implementation examples:
- `openshift_scanner.py` - OpenShift/Kubernetes implementation
- `unix_scanner.py` - Unix/Linux SSH implementation
- `cloud_scanner.py` and `cloud/` - Cloud platform implementations

## Testing

The project includes comprehensive unit and integration tests using pytest.

### Running Tests

```bash
# With virtual environment activated
pytest                    # Run all tests
pytest tests/unit/        # Run only unit tests
pytest tests/integration/ # Run only integration tests
pytest --cov              # Run with coverage report
pytest -v                 # Run with verbose output
```

### Test Coverage

The test suite includes:

- **Unit Tests**: Scanner implementations (Unix, AWS, Azure, GCP, Cloud routing), ScannerFactory, Targets API endpoints, database models
- **Integration Tests**: Full scanner workflows, Targets API with real database

### Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures
├── unit/                    # Unit tests
│   ├── test_unix_scanner.py
│   ├── test_aws_scanner.py
│   ├── test_azure_scanner.py
│   ├── test_gcp_scanner.py
│   ├── test_cloud_scanner.py
│   ├── test_factory.py
│   ├── test_targets_api.py
│   └── test_models.py
└── integration/             # Integration tests
    ├── test_scanner_integration.py
    └── test_targets_api_integration.py
```

### Test Dependencies

Test dependencies are included in `requirements.txt`:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `httpx` - FastAPI test client
- `moto` - AWS service mocking
- `responses` - HTTP mocking

## License

[Your License Here]

