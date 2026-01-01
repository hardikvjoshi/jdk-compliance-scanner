# Import Paths and Module Structure

This document explains how imports work in the backend codebase.

## Directory Structure

All backend code is in the `backend/` folder. The backend folder serves as the Python package root.

```
backend/
├── api/           # FastAPI application and routes
├── auth/          # Authentication module
├── core/          # Core services (database, scanner, compliance)
├── config/        # Configuration management
└── scripts/       # Utility scripts
```

## Import Conventions

### When Running from `backend/` Directory

All imports use absolute imports from the backend root:

```python
# Correct imports (when running from backend/)
from core.database.connection import get_db
from auth.middleware import get_current_active_user
from config.settings import get_settings
from api.routes import clusters
```

### Running the Application

Always run commands from the `backend/` directory:

```bash
cd backend
python run.py              # Run the FastAPI server
python scripts/init_db.py  # Initialize database
```

### Running via uvicorn

When using uvicorn directly, ensure you're in the backend directory:

```bash
cd backend
uvicorn api.main:app --reload
```

The module path `api.main:app` is relative to the current working directory (backend/).

### Running Scripts

Scripts like `scripts/init_db.py` add the backend directory to `sys.path`:

```python
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
```

This ensures imports work correctly even if the script is called from a different directory.

## Package Installation (Optional)

For development, you can install the backend as a package:

```bash
cd backend
pip install -e .
```

This makes the modules available system-wide, but running from the backend directory is still recommended.

## Path References

### Database Path
- Default: `data/compliance.db` (relative to backend/)
- Can be configured via `DB_PATH` environment variable

### Template Path
- Default: `core/reporting/templates` (relative to backend/)
- Can be configured via `REPORT_TEMPLATE_DIR` environment variable

### Environment File
- Location: `.env` in the backend/ directory
- Copy from `env.example` to create

## Key Files

- `run.py`: Main entry point - runs from backend/
- `api/main.py`: FastAPI application - uses relative imports
- `scripts/init_db.py`: Database initialization - adds backend/ to path
- `core/database/connection.py`: Provides `get_db()` FastAPI dependency

## Troubleshooting

### Import Errors

If you get import errors like `ModuleNotFoundError: No module named 'core'`:

1. Ensure you're running from the `backend/` directory
2. Check that `backend/` is in your Python path
3. Verify the file structure matches the expected layout

### Path Issues

If database or template files aren't found:

1. Check that paths are relative to `backend/` directory
2. Verify environment variables are set correctly
3. Ensure directories exist (they're created automatically for the database)

