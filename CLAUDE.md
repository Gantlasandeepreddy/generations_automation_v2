# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-user automation system that extracts client notes from Generations IDB with scheduled and manual execution capabilities.

**Architecture:** FastAPI backend with APScheduler → Selenium automation → JSON audit trail → Excel generation

**Tech Stack:**
- Backend: FastAPI, APScheduler, Selenium, Pydantic
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Storage: JSON files (no database)

## Development Commands

### Setup

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with credentials

# Frontend
cd frontend
npm install
```

### Running Development

**Two terminals required:**

```bash
# Terminal 1: Backend (port 8000)
cd backend
python main.py

# Terminal 2: Frontend (port 3000)
cd frontend
npm run dev
```

### Testing

```bash
# Health check
curl http://localhost:8000/api/health

# API docs (FastAPI Swagger)
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

## Architecture

### Request Flow

```
User → Next.js (localhost:3000) → FastAPI (localhost:8000) → Selenium → Generations IDB
                                        ↓
                                  APScheduler
                                        ↓
                                  JSON audit trail
```

### Key Components

**Backend (`backend/`):**
- `main.py` - FastAPI app, routes, SSE streaming, automation orchestration
- `core/config.py` - Pydantic settings with dynamic paths (project-relative)
- `core/scheduler.py` - APScheduler for weekly/monthly jobs
- `core/session_manager.py` - Generations session keep-alive (5-min ping)
- `db/audit.py` - JSON-based audit trail and logging
- `automation/selenium_helpers.py` - Browser setup, retry decorators
- `automation/report_automation.py` - Login, report export, column selection
- `automation/client_search.py` - Client navigation, personal data extraction
- `automation/data_processing.py` - Excel/HTML to JSON conversion
- `automation/mapping_excel.py` - JSON to Excel template mapping

**Frontend (`frontend/`):**
- `app/page.tsx` - Main tabbed interface (Dashboard, Manual Run, Schedule)
- `components/Dashboard.tsx` - Run history with download links
- `components/ManualRun.tsx` - Manual trigger with SSE log streaming
- `components/ScheduleConfig.tsx` - Weekly/monthly scheduler UI
- `lib/api.ts` - Type-safe API client with SSE support

## Critical Implementation Details

### 1. Function Modification Rule

**CRITICAL:** Always modify existing functions, never create duplicates or backups.

Why: If you create `function_new()` but code still calls `function()`, changes won't apply.

Example:
```python
# ❌ WRONG - Creates duplicate
def export_report_old(...):  # Original
def export_report(...):      # New version - but old one still called

# ✅ CORRECT - Modify existing
def export_report(...):      # Same function, updated logic
```

### 2. Dynamic Path Resolution

All paths are **project-relative** for cross-platform compatibility:

```python
# ✅ CORRECT - Relative to project root
sessions_dir = str(Path(__file__).resolve().parent.parent.parent / "automation_sessions")

# ❌ WRONG - Hardcoded absolute path
sessions_dir = "C:/automation_sessions"
```

**Directory Structure:**
```
project_root/
├── automation_sessions/  # Session data (relative)
├── chrome-profiles/      # Chrome profiles (relative)
├── downloads/            # Output Excel files (relative)
└── backend/
    ├── audit_trail.json  # Audit logs (relative to backend/)
    └── schedule_config.json
```

Can override in `.env` with absolute paths if needed.

### 3. Client Processing Logic

**Scheduled Automation:** Processes **ALL clients** (max_clients=0)
**Manual Automation:** User specifies count (0 = all, N = limit to N)

```python
# In process_clients_from_json()
if max_clients == 0:
    clients_to_process = total_clients  # ALL
else:
    clients_to_process = min(total_clients, max_clients)  # LIMITED
```

**Important:** Scheduled runs ALWAYS process all clients automatically.

### 4. JSON Data Structure

**Client Notes JSON:**
```json
{
  "FirstName": "John",
  "LastName": "Doe",
  "DateofBirth": "01/15/1980",
  "Status": "A",
  "MedicalRec.#": "12345",
  ...
}
```

**Enriched JSON (after processing):**
```json
{
  "FirstName": "John",
  "LastName": "Doe",
  "personal_data": {
    "phone_1": "555-1234",
    "address_1": "123 Main St",
    "city": "Springfield",
    ...
  }
}
```

**Excel generation only processes records with `personal_data` key.**

### 5. Session Keep-Alive Mechanism

Generations IDB logs out after 5 minutes idle.

```python
session = GenerationsSession(driver, credentials, run_id)

# Before each client operation
session.keep_alive()  # Pings if idle > 5 min

# After each operation
session.update_activity()  # Updates timestamp
```

Implementation: Executes `driver.execute_script("return document.readyState")` to keep session alive.

### 6. Date Format Conversion

UI sends dates as `YYYY-MM-DD` (ISO format)
Generations expects `MM/DD/YYYY` (US format)

**Always convert before passing to automation:**

```python
from datetime import datetime
start_obj = datetime.strptime(date_range['start_date'], '%Y-%m-%d')
start_str = start_obj.strftime('%m/%d/%Y')
```

### 7. File Encoding

**Always use UTF-8** (client notes contain special characters):

```python
# Reading
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Writing
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### 8. Selenium Automation Quirks

**Double Page Refresh Required:**
After report export, MUST refresh page twice before navigating to Client List. This is a Generations system quirk.

**JavaScript Click Required:**
Standard `.click()` often fails. Use:
```python
driver.execute_script("arguments[0].click()", element)
```

**Frame Context Switching:**
Generations uses nested iframes. Use `try_switch_to_panel_context()` from `selenium_helpers.py`.

**Stale Element Handling:**
Wrapped with `@retry_on_stale_element` decorator (5 retries with exponential backoff).

**Window Management:**
Each client search opens new tabs. Must track and close properly:
```python
original_window = driver.current_window_handle
# ... open client details in new tab ...
driver.close()  # Close client tab
driver.switch_to.window(original_window)  # Return to main tab
```

### 9. Name Parsing from JSON

Client names in JSON are **separate fields**, not comma-delimited:

```python
# ✅ CORRECT
first_name = client.get('FirstName', '').strip()
last_name = client.get('LastName', '').strip()

# ❌ WRONG - 'Client Name' doesn't exist
client_name = client.get('Client Name', '')
last, first = client_name.split(',')
```

**Handle "ECM" suffix:**
Last names may contain " ECM" suffix (e.g., "Smith ECM"). Strip for search but keep original for matching.

### 10. Path Object vs String Handling

Functions receive Path objects, not strings:

```python
# ✅ CORRECT - Handle Path objects
if isinstance(json_file_path, str):
    enriched_path = json_file_path.replace('.json', '_enriched.json')
else:
    enriched_path = json_file_path.parent / f"{json_file_path.stem}_enriched.json"

# ❌ WRONG - Assumes string
enriched_path = json_file_path.replace('.json', '_enriched.json')
```

## Automation Workflow

### Complete Flow

1. **Login** to Generations IDB
2. **Find** "Client Notes" report in dropdown
3. **Export** report with date range (converts dates to MM/DD/YYYY)
4. **Double refresh** page (Generations system requirement)
5. **Convert** Excel/HTML → JSON (handles HTML tables exported as .xls)
6. **Process clients:**
   - Store original window handle
   - For each client (up to max_clients):
     - Switch to original window
     - Call `keep_alive()` before processing
     - Navigate to Client List (opens new tab)
     - Search by "LastName FirstName"
     - Click client link (opens details tab)
     - Click Personal Data tab
     - Extract 15 personal data fields
     - Close client tabs
     - Update JSON with nested `personal_data`
     - Call `update_activity()` after
7. **Generate** Excel from enriched JSON using template mapping
8. **Save** to `downloads/` directory
9. **Record** in audit trail JSON

### Scheduled Automation Date Ranges

**Weekly:** Last 7 days from execution time
**Monthly:** Last 30 days from execution time

Calculated dynamically in `core/scheduler.py`:
```python
end_date = datetime.now()
start_date = end_date - timedelta(days=7)  # or days=30
```

## Configuration

### Environment Variables

**Required:**
```bash
GENERATIONS_AGENCY_ID=your_agency_id
GENERATIONS_EMAIL=your_email@example.com
GENERATIONS_PASSWORD=your_password

UI_EMAIL=admin@example.com
UI_PASSWORD=changeme
```

**Optional (defaults to project subdirectories):**
```bash
# Only set these for custom absolute paths
SESSIONS_DIR=/custom/path/sessions
CHROME_PROFILES_DIR=/custom/path/profiles

LOG_LEVEL=INFO
```

### Important Constants

- `idle_threshold = 300` - 5 minutes (session timeout)
- `EXPORT_MAX_RETRIES = 7` - Report export attempts
- `DOWNLOAD_TIMEOUT = 180` - File download wait time (seconds)
- `DEFAULT_TIMEOUT = 20` - Element wait timeout (seconds)
- `COLUMN_MAX_RETRIES = 3` - Column selection retries

## API Routes

```
POST   /api/login                         # UI authentication
POST   /api/logout                        # UI logout
GET    /api/health                        # Health + scheduler status
POST   /api/automation/run                # Trigger manual (SSE stream)
GET    /api/automation/history            # Get all runs
GET    /api/automation/download/{run_id}  # Download Excel
GET    /api/schedule                      # Get schedule config
POST   /api/schedule                      # Update schedule (restarts scheduler)
```

**SSE Stream Format:**
```
data: {"type": "log", "message": "Processing client..."}
data: {"type": "status", "status": "completed", "filePath": "...", "runId": "..."}
```

## Frontend State Management

Uses React hooks (`useState`, `useEffect`) with SSE for real-time updates:

```typescript
// SSE connection for live logs
const eventSource = new EventSource(`${API_URL}/api/automation/run`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'log') setLogs(prev => [...prev, data.message]);
  if (data.type === 'status') handleCompletion(data);
};
```

## Brand Colors (Tailwind)

```typescript
colors: {
  primary: '#FF612B',       // Orange - buttons, CTAs
  background: '#FAF8F2',    // Cream - page background
  accent: '#D9F6FA',        // Light blue - progress bars
  navy: '#002677',          // Dark blue - headers
  'brand-gray': '#4B4D4F',  // Gray - body text
}
```

**Important:** Use `brand-gray` not `gray` (conflicts with Tailwind defaults).

## Common Issues

### Client processing skips all clients
- Check JSON field names: Must be `FirstName` and `LastName`, not `Client Name`
- Verify name parsing logic doesn't split by comma

### Automation gets stuck at "Navigating to Client List"
- Each client opens new tabs - must close properly
- Check for "already opened" alerts from duplicate Client List tabs
- Ensure window handle switching before/after each client

### Excel generation processes all 55 clients instead of 2
- Excel mapping must filter: `members = [m for m in all_members if m.get('personal_data')]`
- Only records with enriched `personal_data` should be in Excel

### Path errors (FileNotFoundError with relative paths)
- Pass full Path objects, not strings to functions
- Use `output_dir / filename`, not string concatenation
- Check `.env` doesn't have hardcoded `C:/` paths

### Scheduled automation only processes 10 clients
- Scheduled runs must use `max_clients=0` (ALL clients)
- Manual runs respect user input (0 = all, N = limit)

### Session timeout during long runs
- `keep_alive()` called before each client
- `update_activity()` called after each client
- Check logs for "Keep-alive ping sent"

## Debugging

### Run with visible browser

```python
# In backend/main.py, line ~109
driver = build_driver(download_dir, headless=False)
```

### Check audit trail

```bash
# View all runs with full logs
cat backend/audit_trail.json | python -m json.tool
```

### Check schedule configuration

```bash
cat backend/schedule_config.json
```

### Monitor APScheduler

Backend logs show:
```
INFO - Scheduler started
INFO - Scheduled weekly automation: Day 1 at 09:00
INFO - Running scheduled weekly automation
```

## Code Style

- **Backend:** PEP 8, type hints where helpful, human-readable variable names
- **Frontend:** TypeScript strict mode, explicit types for API responses
- **No duplicate functions:** Modify existing, don't create backups
- **Comments:** Explain "why" and non-obvious behavior, not "what"
- **Logging:** Use `audit_trail.append_log()` for user-facing logs

## Production Deployment

See `README.md` for complete setup instructions including:
- Windows service configuration (NSSM)
- Reverse proxy setup (nginx)
- Firewall rules
- Backup strategies for audit trail and downloads

## Reference Implementation

Root directory contains working **Streamlit code** as reference:
- `/selenium_helpers.py` - Browser setup
- `/report_automation.py` - Login/export flow
- `/client_search.py` - Client processing
- `/data_processing.py` - JSON parsing
- `/main.py` - Complete workflow

When backend automation fails, compare with root Streamlit files to find discrepancies.
