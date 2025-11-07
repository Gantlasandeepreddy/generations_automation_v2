"""
Configuration constants and settings for Client Notes Automation.
"""

# =========================
# Application Configuration
# =========================

# Generations System URLs and Endpoints
LOGIN_URL = "https://generations.idb-sys.com/views/loginnew.aspx"

# =========================
# Element Selectors
# =========================

# Main Navigation
REPORTS_MENU_ID = "aReportMenu"
REPORT_WRITER_XPATH = "//a[contains(@href, 'ReportWriterNew')]"

# Report Configuration
DROPDOWN_ID = "ctl00_MainContent_ddlReportSource"
DISPLAY_BTN_ID = "ctl00_MainContent_btnDisplayReport"
EXPORT_BTN_ID = "btnExportExcel"

# Date Selection
DATE_PANEL_ID = "ctl00_MainContent_Panel1"
START_DATE_ID = "ctl00_MainContent_txtAuthStartDate"
END_DATE_ID = "ctl00_MainContent_txtAuthEndDate"
DATE_OK_BTN_ID = "ctl00_MainContent_btnOK"

# Client Notes Specific Elements
CLIENT_STATUS_DROPDOWN_ID = "ctl00_MainContent_ddlClientType"
PAYOR_DROPDOWN_ID = "ctl00_MainContent_ddlPayorType"
COLUMN_CHOOSER_BTN_ID = "ctl00_MainContent_imgColumnChooser"

# Client Search Elements
CLIENTS_MENU_ID = "mnClients"
CLIENT_LIST_LINK_ID = "menuClientList"
SEARCH_BOX_ID = "txtSearch"
SEARCH_BUTTON_ID = "btnSearch"
CLIENT_TYPE_DROPDOWN_ID = "ctl00_MainContent_ddlType"
CLIENT_NAME_LINK_XPATH = "//a[contains(@onclick, 'fnShowClientDetails')]"

# Personal Data Elements
PERSONAL_DATA_TAB_ID = "ctl00_MainContent_tdPersonalData"

# =========================
# Application Settings
# =========================

# Target Report
TARGET_REPORT_NAME = "Client Notes"

# Required Columns for Client Notes Report
REQUIRED_COLUMNS = [
    "Client Type", "Date of Birth", "Note Type", "Note Descr", 
    "First Name", "Last Name", "LocationID", "Medical Rec. #", "Status"
]

# Personal Data Field Mappings
PERSONAL_DATA_FIELDS = {
    'phone_1': 'ctl00_MainContent_PersonalData_txtPhone',
    'phone_2': 'ctl00_MainContent_PersonalData_txtPhone2', 
    'service_start': 'ctl00_MainContent_PersonalData_txtServiceStartDate',
    'service_end': 'ctl00_MainContent_PersonalData_txtServiceEndDate',
    'inquiry_date': 'ctl00_MainContent_PersonalData_txtInquiryDate',
    'assessment': 'ctl00_MainContent_PersonalData_txtAssesmentDate',
    'case_manager': 'ctl00_MainContent_PersonalData_dpCaseManager',
    'med_record': 'ctl00_MainContent_PersonalData_txtMedRecord',
    'referral_number': 'ctl00_MainContent_PersonalData_txtReferral',
    'address_1': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_txtAddress1',
    'address_2': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_txtAddress2',
    'city': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_txtCity',
    'state': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_txtProv',
    'zip': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_txtPC',
    'county': 'ctl00_MainContent_PersonalData_addresstab_homeaddressTab_dpCounty'
}

# =========================
# Default Settings
# =========================

# Browser Configuration
DEFAULT_HEADLESS = True
DEFAULT_STEP_DELAY = 2.0
MAX_STEP_DELAY = 1.0  # Cap for step delays

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
EXPORT_MAX_RETRIES = 7
COLUMN_MAX_RETRIES = 3
STALE_ELEMENT_RETRIES = 5

# Timeout Settings
DEFAULT_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 180
FRAME_TIMEOUT = 5
ELEMENT_TIMEOUT = 10

# File Handling
MAX_FILENAME_LENGTH = 180
MAX_CLIENTS_PER_BATCH = 10

# Streamlit Configuration
DEFAULT_PORT = 8511
PAGE_TITLE = "Client Notes Downloader"
PAGE_ICON = "[STATS]"
LAYOUT = "centered"
