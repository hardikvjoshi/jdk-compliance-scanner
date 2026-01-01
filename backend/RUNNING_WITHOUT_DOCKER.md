# Running Without Docker

This application is designed to run directly on your local machine or server **without requiring Docker**. All dependencies are Python packages that can be installed via pip.

## Why No Docker Required?

The application uses:
- **SQLite** - File-based database, no external database server needed
- **FastAPI** - Python web framework, runs directly with uvicorn
- **Python packages** - All dependencies installable via pip
- **Local file storage** - Database and configuration files stored locally

## Quick Start

### 1. System Requirements

- **Python 3.8 or higher** (check with `python3 --version`)
- **pip** (Python package manager, usually included with Python)
- **SQLite** (usually included with Python)

### 2. Installation Steps

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (required)
python3 -m venv .venv

# Activate virtual environment
# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env
# Edit .env with your settings

# Initialize database
python scripts/init_db.py

# Run the server
python run.py
```

**Note**: All commands must be run with the virtual environment activated. The `.venv` directory is git-ignored by default (standard convention).

### 3. Using the Quick Start Scripts

For convenience, use the provided startup scripts (they handle virtual environment automatically):

**Linux/Mac:**
```bash
cd backend
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
cd backend
start.bat
```

These scripts will:
- Check Python installation
- Create `.venv` virtual environment if it doesn't exist
- Activate the virtual environment
- Create .env file if missing
- Install dependencies into `.venv` if missing
- Initialize database if needed
- Start the server

## Configuration

All configuration is done via environment variables in the `.env` file:

```bash
# Minimal required configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_PASSWORD=your-encryption-password

# Optional configuration
DB_PATH=data/compliance.db          # Database file path (relative to backend/)
DEBUG=False                          # Debug mode
DEFAULT_THREAD_COUNT=5              # Parallel scan threads
ADMIN_PASSWORD=admin                # Initial admin password
```

## File Structure (Local Run)

When running without Docker, files are stored locally:

```
backend/
├── .venv/                     # Virtual environment (git-ignored, created automatically)
├── data/
│   └── compliance.db          # SQLite database (created automatically)
├── .env                       # Configuration (create from env.example)
├── core/
│   └── reporting/
│       └── templates/         # Report templates
└── logs/                      # Log files (if logging configured)
```

## Running in Production (Without Docker)

For production deployment without Docker:

### Option 1: Direct Python Execution

```bash
# Using uvicorn with production settings
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/jdk-scanner.service`:

```ini
[Unit]
Description=JDK Compliance Scanner API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/jdk-compliance-scanner/backend
Environment="PATH=/path/to/jdk-compliance-scanner/backend/.venv/bin"
ExecStart=/path/to/jdk-compliance-scanner/backend/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable jdk-scanner
sudo systemctl start jdk-scanner
```

### Option 3: Process Manager (PM2, Supervisor, etc.)

Using PM2:
```bash
cd backend
# Ensure virtual environment is activated in the shell
source .venv/bin/activate
pm2 start "uvicorn api.main:app --host 0.0.0.0 --port 8000" --name jdk-scanner --interpreter .venv/bin/python
pm2 save
pm2 startup
```

## Database Management

The SQLite database file is located at `data/compliance.db` (or path specified in `DB_PATH`).

### Backup Database

```bash
# Simple copy
cp data/compliance.db data/compliance.db.backup

# With timestamp
cp data/compliance.db data/compliance.db.$(date +%Y%m%d_%H%M%S).backup
```

### Restore Database

```bash
cp data/compliance.db.backup data/compliance.db
```

### Reset Database

```bash
# Remove database file
rm data/compliance.db

# Reinitialize
python scripts/init_db.py
```

## Troubleshooting

### Python Version Issues

Ensure you have Python 3.8+:
```bash
python3 --version
```

If you have multiple Python versions:
```bash
# Create venv with specific Python version
python3.9 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Permission Issues

If you get permission errors:
```bash
# Use virtual environment (required)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is in use:
```bash
# Use a different port
uvicorn api.main:app --port 8001

# Or find and kill the process using port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Locked

If you get "database is locked" errors:
- Ensure only one instance of the application is running
- Check for other processes accessing the database file
- Restart the application

## Virtual Environment (Required)

This application **requires** a virtual environment (`.venv`) for all executions. Using a virtual environment isolates dependencies and ensures reproducible environments.

### Why `.venv`?

- **Standard convention**: `.venv` is commonly used and git-ignored by default
- **Clear identification**: The dot prefix indicates it's a hidden/system directory
- **Git-friendly**: Most `.gitignore` templates already include `.venv`
- **Project-local**: Keeps all dependencies within the project directory

### Creating and Using Virtual Environment

```bash
# Create virtual environment
cd backend
python3 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py

# Deactivate when done
deactivate
```

### Important Notes

- **Always activate** the virtual environment before running any Python commands
- The startup scripts (`start.sh`/`start.bat`) automatically handle virtual environment creation and activation
- If you see "command not found" errors, ensure the virtual environment is activated
- The `.venv` directory should **not** be committed to git (it's git-ignored by default)

## Advantages of Running Without Docker

1. **Simpler setup** - Just Python and pip needed (virtual environment handles isolation)
2. **Easier debugging** - Direct access to Python debugger
3. **Faster development** - No container build time
4. **Lower resource usage** - No container overhead
5. **Better IDE integration** - Direct file access for debugging
6. **Native performance** - No container layer overhead
7. **Isolated dependencies** - Virtual environment (`.venv`) provides dependency isolation without Docker

## When to Use Docker (Optional)

Docker is optional but can be useful for:
- Consistent deployment across environments
- Isolation from system Python packages
- Easy scaling with orchestration (Kubernetes, Docker Swarm)
- Production deployments with complex infrastructure

But for development and simple deployments, running without Docker is perfectly fine and often preferred!

