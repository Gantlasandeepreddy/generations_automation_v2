# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI + Next.js automation tool that extracts client notes from Generations IDB system. Migrated from Streamlit to enable 5-10 concurrent users with background job processing.

**Architecture:** FastAPI backend → Huey workers (SQLite queue) → Selenium automation → Excel generation

## Development Commands

### Setup

```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running Development Environment

**Three terminals required:**

```powershell
# Terminal 1: API Server (port 8000)
cd backend
.\venv\Scripts\python.exe start_api.py

# Terminal 2: Background Worker
cd backend
.\venv\Scripts\python.exe start_worker.py

# Terminal 3: Frontend (port 3000)
cd frontend
npm run dev
```

### Testing

```powershell
# Health check
curl http://localhost:8000/health

# API docs (Swagger)
# Open: http://localhost:8000/docs

# Database inspection
cd backend
.\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('jobs.db'); print(conn.execute('SELECT job_id, status, total_clients, processed_clients FROM jobs ORDER BY created_at DESC LIMIT 5').fetchall())"

# Frontend
# Open: http://localhost:3000
```

### Build Production

```powershell
# Frontend
cd frontend
npm run build
npm run start

# Backend (no build step, runs via uvicorn)
```

## Architecture Overview

### Request Flow

```
Browser (Next.js) → FastAPI API → Huey Queue → Worker Process
                                        ↓
                                   Selenium → Generations IDB
                                        ↓
                                   SQLite DB (status/logs)
```

### Key Components

1. **FastAPI API** (`backend/main.py`): REST endpoints for auth, job submission, status polling, file downloads
2. **Huey Worker** (`backend/workers/`): Background job processor with SQLite queue
3. **Session Manager** (`backend/core/session_manager.py`): Keep-alive pings every 5 min to prevent Generations timeout
4. **Automation Layer** (`backend/automation/`): Selenium scripts (from original Streamlit project)
5. **Next.js Frontend** (`frontend/`): 4-step wizard UI with real-time status polling

### Database Structure

**SQLite (`jobs.db`):**
- `jobs` table: job_id, status, user_email, client counts, file paths, logs
- Status values: `queued` → `processing` → `completed` or `failed`
- Logs stored as append-only text field

**SQLite (`jobs_queue.db`):**
- Managed by Huey
- Stores queued tasks and results

## Critical Implementation Details

### Import Path Handling

**CRITICAL:** All entry point files MUST include dynamic path setup:

```python
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent  # or .parent.parent for nested files
sys.path.insert(0, str(backend_dir))

# Now imports work regardless of CWD
from core.config import settings
```

**Files with this pattern:**
- `backend/main.py`
- `backend/start_api.py`
- `backend/start_worker.py`
- `backend/workers/automation_worker.py`
- `backend/workers/tasks.py`

**Why:** Allows running scripts from any directory without ModuleNotFoundError.

### Session Keep-Alive Mechanism

**Problem:** Generations IDB logs out after ~5 minutes of idle time.

**Solution:** `GenerationsSession` class in `backend/core/session_manager.py`:

```python
# Before each client operation:
session.keep_alive()  # Pings if idle > 5 minutes
session.update_activity()  # Updates timestamp after operation

# Automatic re-login (3 attempts) if session dies:
session.relogin()
```

**Implementation:** Executes lightweight JavaScript to keep session alive:
```python
driver.execute_script("return document.readyState")
```

### Selenium Automation Quirks

1. **Double Page Refresh Required:**
   - After report export, MUST refresh page twice before navigating to Client List
   - This is a Generations system quirk, not a bug
   - Don't remove this behavior

2. **Frame Context Switching:**
   - Generations uses nested iframes
   - Use `try_switch_to_panel_context()` helper from `selenium_helpers.py`
   - Always fallback to main content

3. **JavaScript Click Required:**
   - Standard `.click()` often fails
   - Use: `driver.execute_script("arguments[0].click()", element)`

4. **Stale Element Handling:**
   - Wrapped with `@retry_on_stale_element` decorator (5 retries)
   - Applied to all element interactions

### Organization Brand Colors

**Defined in `frontend/tailwind.config.ts`:**

```typescript
colors: {
  primary: '#FF612B',       // Orange - buttons, CTAs
  background: '#FAF8F2',    // Cream - page background
  accent: '#D9F6FA',        // Light blue - progress bars
  navy: '#002677',          // Dark blue - headers
  'brand-gray': '#4B4D4F',  // Gray - body text (NOT 'gray'!)
}
```

**Important:** Don't use `gray` as custom color name - conflicts with Tailwind's default gray scale.

### Module-Level Code Anti-Pattern

**Problem:** Original `mapping2excel.py` had file I/O at module level, causing imports to fail.

**Solution:** All file operations wrapped in `generate_excel_from_json()` function.

**Rule:** When migrating from Streamlit or adding new automation modules:
- Avoid module-level I/O operations
- Use function parameters instead of file system scanning
- Explicitly pass file paths from caller

## File Organization

### Backend Structure

```
backend/
├── api/                    # FastAPI route handlers
│   ├── auth.py            # POST /api/auth/validate
│   ├── jobs.py            # Job submission, status, cancel
│   └── files.py           # File downloads
├── automation/            # Selenium automation (copied from root)
│   ├── config.py          # Element selectors, timeouts, batch limits
│   ├── selenium_helpers.py # Browser setup, retry logic
│   ├── report_automation.py # Login, export report workflow
│   ├── client_search.py   # Client search, personal data extraction
│   ├── data_processing.py # File conversion utilities
│   └── mapping_excel.py   # JSON → KP Excel template
├── core/                  # Infrastructure
│   ├── config.py          # Settings (Pydantic)
│   ├── security.py        # JWT encode/decode
│   ├── queue.py           # Huey configuration
│   └── session_manager.py # Keep-alive mechanism
├── db/                    # Database
│   ├── database.py        # Schema initialization
│   └── crud.py            # All database operations
├── workers/               # Background processing
│   ├── tasks.py           # Main automation workflow
│   └── automation_worker.py # Huey consumer entry point
└── main.py                # FastAPI app
```

### Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx           # Main wizard with step management
│   └── globals.css        # Tailwind + brand colors
├── components/wizard/
│   ├── StepLogin.tsx      # Credential validation
│   ├── StepConfigure.tsx  # Date range picker
│   ├── StepProcess.tsx    # Job status polling
│   └── StepDownload.tsx   # Excel download
└── lib/
    ├── api.ts             # Typed API client
    └── auth.ts            # JWT storage (localStorage)
```

## Key Configuration Files

### Backend `.env`

```
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
SESSIONS_DIR=C:/automation_sessions
CHROME_PROFILES_DIR=C:/chrome-profiles
DATABASE_PATH=jobs.db
QUEUE_DATABASE_PATH=jobs_queue.db
MAX_CONCURRENT_WORKERS=10
LOG_LEVEL=INFO
```

### Frontend `.env.local`

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Automation Constants (`backend/automation/config.py`)

```python
MAX_CLIENTS_PER_BATCH = 10  # Don't increase without testing keep-alive
DOWNLOAD_TIMEOUT = 180       # Seconds to wait for report download
DEFAULT_TIMEOUT = 20         # Element wait timeout
EXPORT_MAX_RETRIES = 7       # Export operation retries
```

## Automation Workflow

**End-to-End Process:**

1. **Login** (`report_automation.py:login_and_open_report_writer()`)
   - Navigate to Generations IDB
   - Authenticate with credentials
   - Open Report Writer tab

2. **Export Report** (`report_automation.py:export_single_report()`)
   - Select "Client Notes" report
   - Set date range, filters, columns
   - Download as Excel/HTML
   - Convert to JSON

3. **Refresh Page Twice** (Required!)
   - Generations system quirk
   - Must refresh before client navigation

4. **Process Clients** (Max 10 per batch)
   - For each client:
     - Navigate to Client List
     - Search by name
     - Extract personal data (15 fields)
     - Update JSON with nested `personal_data` object
     - **Keep-alive ping before each client**

5. **Generate Excel** (`mapping_excel.py:generate_excel_from_json()`)
   - Map JSON to KP template columns
   - Save to session output directory
   - Return file path

## Common Issues & Fixes

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'core'`

**Fix:** Add dynamic path setup to file (see "Import Path Handling" above)

### Tailwind Build Error

**Error:** `The 'border-gray-300' class does not exist`

**Fix:** Already fixed. Don't use `gray` as custom color - use `brand-gray`.

### Exit on Import

**Error:** `SystemExit: 1` when importing `mapping_excel.py`

**Fix:** Already fixed. All logic wrapped in `generate_excel_from_json()` function.

### Session Timeout

**Error:** Job fails with "Session expired"

**Fix:** Check `idle_threshold` in `session_manager.py` (default 300 seconds). Worker calls `keep_alive()` before each operation.

### Database Locked

**Error:** `database is locked`

**Fix:** Stop all services, delete `jobs.db-shm` and `jobs.db-wal`, restart.

## Windows Deployment

**See:** `DEPLOYMENT.md` for complete Windows VM setup with NSSM services.

**Quick Reference:**
- Service 1: GenerationsAPI (uvicorn)
- Service 2: GenerationsWorker (Huey consumer)
- Service 3: GenerationsFrontend (Next.js)
- Task Scheduler: Daily cleanup of old session folders

## Testing Workflow

1. Start all 3 services (API, worker, frontend)
2. Open http://localhost:3000
3. Step 1: Enter Generations credentials → Validate
4. Step 2: Select date range (e.g., last 7 days)
5. Step 3: Submit job → Watch real-time logs (polls every 3 seconds)
6. Step 4: Download Excel file

## Related Documentation

- `MIGRATION_GUIDE.md` - Streamlit → FastAPI migration details
- `DEPLOYMENT.md` - Windows VM production deployment
- `TROUBLESHOOTING.md` - Common issues and solutions
- `IMPLEMENTATION_SUMMARY.md` - Migration status and checklist
- `README_NEW.md` - Quick start guide

## Important Constants

### Batch Processing
- **Max clients per job:** 10 (prevents timeout)
- **Keep-alive interval:** 5 minutes (300 seconds)
- **Re-login attempts:** 3

### Timeouts
- **Download timeout:** 180 seconds
- **Element wait:** 20 seconds
- **Export retries:** 7 attempts

### File Paths
- **Session directories:** `C:/automation_sessions/{job_id}/`
- **Chrome profiles:** `C:/chrome-profiles/{job_id}/`
- **Downloads:** `{session_dir}/downloads/`
- **Output:** `{session_dir}/output/`

## Code Style Notes

- **Backend:** Human-readable Python, avoid AI patterns
- **Frontend:** TypeScript with explicit types
- **No duplicate functions:** Modify existing code, don't create backups
- **Comments:** Explain "why", not "what"
- **Logging:** Use `crud.append_log()` for job logs, not print statements

## Critical Rules

1. **Never remove double page refresh** - it's a Generations quirk, not a bug
2. **Always call `session.keep_alive()`** before long operations
3. **Use `brand-gray` not `gray`** in Tailwind colors
4. **Add path setup** to any new entry point file
5. **Wrap all I/O** in functions, not module level
6. **Test with real credentials** - mocking won't catch Generations quirks
7. **Max 10 clients per batch** - hardcoded for session stability
8. **Run worker from backend directory** - queue database location dependent
