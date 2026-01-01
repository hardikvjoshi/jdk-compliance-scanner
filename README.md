# JDK Compliance Scanner

A web-based application for checking JDK compliance across OpenShift clusters (Dev/UAT/Production) with extensible scanner architecture.

## Overview

This application provides:
- REST API backend for managing clusters, projects, scans, and compliance
- Web-based UI for configuration, scanning, and reporting
- Support for multiple deployment types (OpenShift, UNIX, Windows, Cloud)
- Comprehensive reporting with email delivery
- Exemption management
- Automated scaling of non-compliant applications

## Project Structure

```
jdk-compliance-scanner/
├── docs/                    # Documentation
│   ├── jdk_compliance_scanner_c2454e26.plan.md  # Implementation plan
│   └── jdk_compliance_scanner_ui_plan.md        # UI plan
├── backend/                 # Backend API
│   ├── api/                # API routes and application
│   ├── auth/               # Authentication module
│   ├── core/               # Core services (database, scanner, compliance)
│   ├── config/             # Configuration management
│   └── scripts/            # Utility scripts
├── ui/                      # Frontend UI (to be created)
└── README.md               # This file
```

## Getting Started

### Backend Setup

See [backend/README.md](backend/README.md) for detailed backend setup instructions.

Quick start:
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python scripts/init_db.py
python run.py
```

The API will be available at `http://localhost:8000` with Swagger docs at `/docs`

## Documentation

- **Implementation Plan**: `docs/jdk_compliance_scanner_c2454e26.plan.md`
- **UI Plan**: `docs/jdk_compliance_scanner_ui_plan.md`
- **Backend README**: `backend/README.md`

## Status

### Backend
- [x] Database schema and models
- [x] Database connection (SQLite)
- [x] Credential encryption
- [x] Authentication (JWT)
- [x] Cluster management API
- [x] Project onboarding API
- [x] JDK versions management API
- [x] Scanner architecture (BaseScanner, Factory, OpenShiftScanner)
- [x] JDK detection engine
- [x] Compliance checker
- [x] Parallel executor
- [ ] Scanning API endpoints
- [ ] Exemption management API
- [ ] Scaling manager
- [ ] Reporting engine
- [ ] Docker setup

### UI
- [ ] UI implementation

---

**Note**: Previous implementation is archived in `/home/hardik/Dev/31DEC25`





