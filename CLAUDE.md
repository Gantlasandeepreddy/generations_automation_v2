# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Streamlit-based web automation tool** that automates the extraction of client notes from the Generations IDB system. It uses Selenium WebDriver to log in, navigate reports, export data, and extract personal information from client records.

**Core workflow:**
1. User connects to Generations system via Streamlit UI
2. Exports "Client Notes" report (Excel/JSON) for a date range
3. Automatically searches for each client and extracts personal data
4. Converts JSON data to Excel format using a Kaiser Permanente (KP) template

## Development Commands

### Running the Application
```bash
# Run Streamlit app (default port 8511)
streamlit run main.py --server.port 8511

# Run with auto-reload during development
streamlit run main.py --server.port 8511 --server.runOnSave true
```

### Environment Setup
```bash
# Install dependencies using pip
pip install -r requirements.txt

# Or using uv (if available)
uv sync
```

### Configuration
- Credentials are read from `.env` file or Streamlit secrets
- `.env` format: `AGENCY_ID`, `EMAIL`, `PASSWORD`

## Architecture

### Module Structure

**main.py** - Entry point and orchestration
- Streamlit app initialization and UI workflow
- `connect_and_load()`: Authenticates and loads Report Writer
- `process_all_clients_automatically()`: Batch processes clients from JSON
- `refresh_page_twice_and_prepare()`: Required page refresh after export

**config.py** - Centralized configuration
- All element selectors (IDs, XPATHs) for the Generations system
- Timeout settings, retry counts, file handling constants
- `MAX_CLIENTS_PER_BATCH = 10`: Limits batch processing size

**selenium_helpers.py** - Browser automation utilities
- `build_driver()`: Creates Chrome WebDriver with download preferences
- `wait_document_ready()`: Waits for page load with alert handling
- `handle_warning_popups()`: Dismisses JavaScript alerts
- `retry_on_stale_element()`: Decorator for handling stale elements
- Frame navigation helpers: `try_switch_to_panel_context()`, `find_element_in_any_frame()`

**report_automation.py** - Report generation workflow
- `login_and_open_report_writer()`: Authenticates to Generations
- `find_client_notes_report()`: Locates the "Client Notes" report in dropdown
- `export_single_report()`: Handles report export with retry logic
- Column selection and date range configuration

**client_search.py** - Client navigation and data extraction
- `navigate_to_clients()`: Navigates to Clients → Client List
- `process_client_with_personal_data()`: Searches for client and extracts personal data
- Extracts: phone numbers, service dates, inquiry date, assessment date, addresses
- Uses `PERSONAL_DATA_FIELDS` mapping from config.py

**data_processing.py** - File conversion and data management
- `convert_excel_to_json()`: Converts HTML/Excel exports to JSON
- `get_clients_from_json_file()`: Parses exported JSON and extracts unique clients
- `update_json_with_personal_data()`: Appends extracted personal data to JSON
- `manage_output_folders()`: Creates/manages `downloads/` and `historic_outputs/` directories

**ui_components.py** - Streamlit UI components
- `setup_streamlit_page()`: Page configuration
- `render_sidebar()`: Credentials and browser settings
- `render_date_range_selector()`: Date picker for report range
- `display_client_data()`: Shows extracted personal information
- Session state management

**mapping2excel.py** - JSON to Excel conversion
- Reads JSON from `downloads/` directory
- Maps JSON fields to KP Excel template columns (see `mappings_gen_report`)
- Outputs: `ECM_KP_RTF_Template_Populated_<filename>.xlsx`
- Run standalone: `python mapping2excel.py`

### Key Workflow Patterns

**Session State Management (Streamlit)**
- `st.session_state.driver`: Active Selenium WebDriver
- `st.session_state.client_notes_value/text`: Selected report details
- `st.session_state.download_dir`: Temp directory for browser downloads
- `st.session_state.automation_running`: Controls batch processing flag

**Selenium Retry Strategy**
- Stale element retries: Use `@retry_on_stale_element` decorator
- Export retries: `EXPORT_MAX_RETRIES = 7` in config.py
- Frame context handling: `try_switch_to_panel_context()` with fallback to main content

**Browser Tab Management**
- Original tab handle stored before client searches
- Client details open in new tabs/windows
- Always return to original tab after each client using `driver.switch_to.window(original_tab)`

**File Organization**
- `downloads/`: Final JSON and Excel outputs
- `historic_outputs/`: (Currently unused, reserved for archiving)
- Temporary download directory: `tempfile.mkdtemp(prefix="dl_")`

## Important Implementation Notes

### Generations System Quirks

1. **Required Page Refreshes**: After report export, must refresh page **twice** before client navigation (see `refresh_page_twice_and_prepare()`)

2. **Frame Context Issues**: Generations uses complex iframe structures. Always use frame helpers from selenium_helpers.py rather than direct frame switching.

3. **JavaScript Click Requirements**: Many elements require `driver.execute_script("arguments[0].click()")` instead of `.click()`

4. **Alert Handling**: Frequent JavaScript alerts/warnings - use `handle_warning_popups()` liberally

### Data Extraction Logic

- **Client Name Matching**: JSON export contains "Full Name", parsed into "First Name", "Last Name", and "Original Last Name" (handles hyphenated names)
- **Personal Data Fields**: Defined in `PERSONAL_DATA_FIELDS` dict in config.py - maps field names to element IDs
- **Batch Limit**: Processing limited to `MAX_CLIENTS_PER_BATCH = 10` to avoid timeouts

### Excel Mapping Logic (mapping2excel.py)

- **Age Group Conversion**: Date of Birth → Binary age group classification
- **Conditional Fields**: Some fields only populated if specific note types exist (see `conditional_mapping`)
- **Note Description Parsing**: Several fields deferred to note description text (see `note_desc_fields`)

## Credentials & Security

- **Never commit** `.env` file or credentials
- Credentials loaded via: `python-dotenv` → `.env` file or Streamlit secrets
- `.gitignore` should include: `.env`, `downloads/`, `historic_outputs/`, `__pycache__/`

## Troubleshooting

### Common Issues

1. **"Failed to connect or find Client Notes report"**
   - Check credentials in sidebar
   - Try running non-headless (`headless=False`) to see browser
   - Verify Report Writer tab opened successfully

2. **Stale Element Exceptions**
   - Already handled by `@retry_on_stale_element` in most places
   - If adding new element interactions, use the decorator

3. **Client Search Failures**
   - Check `CLIENT_TYPE_DROPDOWN_ID` is set to correct value
   - Ensure page refreshed twice before navigation
   - Original tab handle may be lost - check window_handles

4. **Download Not Found**
   - Increase `DOWNLOAD_TIMEOUT` in config.py
   - Check Chrome download preferences in `build_driver()`
   - Verify temp directory permissions

### Debug Mode

Set `headless = False` in sidebar to watch browser automation in real-time. Debug information displayed in Streamlit expanders on errors.
