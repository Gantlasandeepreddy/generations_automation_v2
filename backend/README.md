# Backend - Generations Automation API

FastAPI-based backend for the Generations automation tool.

## Quick Start

### Install Dependencies
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment
Create `.env` file:
```
# Generations IDB Credentials
GENERATIONS_AGENCY_ID=your_agency_id
GENERATIONS_EMAIL=your_email@example.com
GENERATIONS_PASSWORD=your_password

# UI Login
UI_EMAIL=admin@example.com
UI_PASSWORD=changeme

# Directory Paths (Optional - defaults to project subdirectories)
# SESSIONS_DIR=/path/to/automation_sessions
# CHROME_PROFILES_DIR=/path/to/chrome-profiles

LOG_LEVEL=INFO
```

### Run Development Server

```powershell
# Terminal 1 - API Server
uv run main.py

# Terminal 2 - Worker
uv run workers/automation_worker.py

# Or with venv directly
.\venv\Scripts\python.exe main.py
.\venv\Scripts\python.exe workers\automation_worker.py
```

### Test API
```powershell
# Health check
curl http://localhost:8000/health

# API docs
# Open browser: http://localhost:8000/docs
```

## Project Structure

```
backend/
├── api/              # FastAPI endpoints
├── automation/       # Selenium automation (from original project)
├── core/             # Config, security, session manager
├── db/               # SQLite database operations
├── models/           # Pydantic models
├── workers/          # Huey background tasks
├── main.py           # FastAPI application
└── requirements.txt
```

## Running from Any Directory

All scripts automatically add the backend directory to Python path, so you can run them from anywhere:

```powershell
# From project root with uv
cd /path/to/project
uv run backend/main.py
uv run backend/workers/automation_worker.py

# From backend directory
cd backend
uv run main.py
uv run workers/automation_worker.py
```

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /api/auth/validate` - Validate Generations credentials
- `POST /api/jobs/submit` - Submit automation job
- `GET /api/jobs/{id}/status` - Get job status
- `GET /api/files/{id}/download` - Download Excel file

## Troubleshooting

### Module not found errors
The scripts now automatically add the backend directory to Python path. If you still get import errors:
1. Make sure you're using `uv run` or the venv Python: `.\venv\Scripts\python.exe`
2. **CRITICAL**: Check that the worker imports tasks: `from workers import tasks` (required for Huey to register the task functions)

### Database locked
Stop all services and delete lock files:
```powershell
del jobs.db-shm jobs.db-wal
```

### Chrome not found
Install Chrome browser or update selenium:
```powershell
pip install --upgrade selenium webdriver-manager
```

## Production Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for Windows service setup.
