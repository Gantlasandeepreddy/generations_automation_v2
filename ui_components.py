"""
Streamlit UI components and helper functions.
Handles user interface elements, session management, and display functions.
"""

import os
import streamlit as st
from pathlib import Path
from datetime import date as _date, timedelta

from config import PAGE_TITLE, PAGE_ICON, LAYOUT, MAX_CLIENTS_PER_BATCH


def setup_streamlit_page():
    """Initialize Streamlit page configuration."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)
    st.title(f"{PAGE_ICON} Client Notes Downloader")


def get_secret_or_env(key: str, default: str = "") -> str:
    """Safe accessor: use st.secrets if present, else env vars, else default."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def render_sidebar():
    """Render the sidebar with credentials and settings."""
    with st.sidebar:
        st.header("🔐 Credentials & Settings")

        # Credentials section
        agency_id = st.text_input(
            "Agency ID", 
            value=get_secret_or_env("AGENCY_ID", ""),
            help="You can also set env var AGENCY_ID or put this in .streamlit/secrets.toml"
        )
        email = st.text_input("Email / Username", value=get_secret_or_env("EMAIL", ""))
        password = st.text_input(
            "Password", 
            value=get_secret_or_env("PASSWORD", ""), 
            type="password"
        )

        # Browser settings
        headless = st.checkbox(
            "Run Chrome headless", 
            value=False, 
            help="Uncheck to watch the browser for debugging."
        )
        slow_step_delay = st.slider(
            "Step delay (seconds)", 
            min_value=0.0, 
            max_value=5.0, 
            value=2.0, 
            step=0.5,
            help="Extra pause after dropdown & calendar actions to allow UI to load."
        )
        
        st.caption("Tip: Increase the delay if the calendar or export steps are slow.")
        st.divider()
        st.caption("Credentials are used locally in this session only.")

    return agency_id, email, password, headless, slow_step_delay


def render_connection_buttons(connect_callback, disconnect_callback):
    """Render connection and disconnection buttons."""
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "🔌 Connect & Load Reports", 
            use_container_width=True, 
            type="primary", 
            on_click=connect_callback
        )
    with col2:
        st.button("🔴 Disconnect", use_container_width=True, on_click=disconnect_callback)


def render_folder_metrics(downloads_folder, historic_folder):
    """Render folder management metrics."""
    if downloads_folder and historic_folder:
        downloads_count = len(list(downloads_folder.glob("*"))) if downloads_folder.exists() else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📁 Current Downloads", downloads_count, help="Files in ./downloads/ folder")
        with col2:
            historic_sessions = len(list(historic_folder.glob("session_*"))) if historic_folder.exists() else 0
            st.metric("🗂️ Historic Sessions", historic_sessions, help="Previous export sessions in ./historic_outputs/")


def render_date_range_selector():
    """Render date range selection interface."""
    today = _date.today()
    default_start = today.replace(day=1)
    default_end = today
    
    # Set a reasonable minimum date (e.g., 2 years back)
    min_date = today - timedelta(days=730)  # Approximately 2 years back
    
    st.write("📅 **Date Range Selection**")
    
    dr = st.date_input(
        "Select start and end dates for Client Notes report", 
        value=(default_start, default_end),
        min_value=min_date,   # Prevent selection of very old dates
        max_value=today,      # Restrict to today and earlier dates only
        help=f"📊 Date range is restricted to prevent future dates and very old records. Range: {min_date.strftime('%m/%d/%Y')} → {today.strftime('%m/%d/%Y')}"
    )
    
    return normalize_date_range(dr)


def normalize_date_range(dr) -> tuple[_date, _date]:
    """
    Accepts a single date, or a sequence (tuple/list) of dates from st.date_input,
    and returns a (start_date, end_date) tuple of datetime.date.
    Validates that dates are not in the future.
    """
    today = _date.today()
    
    if isinstance(dr, _date):
        # Ensure single date is not in the future
        validated_date = min(dr, today)
        if dr > today:
            st.warning(f"⚠️ Future date {dr.strftime('%Y-%m-%d')} adjusted to today ({today.strftime('%Y-%m-%d')})")
        return validated_date, validated_date
        
    if isinstance(dr, (list, tuple)):
        vals = [d for d in dr if isinstance(d, _date)]
        if len(vals) >= 2:
            start_date = min(vals[0], today)
            end_date = min(vals[1], today)
            
            # Show warnings if future dates were selected
            if vals[0] > today:
                st.warning(f"⚠️ Future start date {vals[0].strftime('%Y-%m-%d')} adjusted to today ({today.strftime('%Y-%m-%d')})")
            if vals[1] > today:
                st.warning(f"⚠️ Future end date {vals[1].strftime('%Y-%m-%d')} adjusted to today ({today.strftime('%Y-%m-%d')})")
                
            return start_date, end_date
            
        if len(vals) == 1:
            validated_date = min(vals[0], today)
            if vals[0] > today:
                st.warning(f"⚠️ Future date {vals[0].strftime('%Y-%m-%d')} adjusted to today ({today.strftime('%Y-%m-%d')})")
            return validated_date, validated_date
            
    # Fallback to current month if no valid dates
    return today.replace(day=1), today


def render_automation_checkbox():
    """Render automation control checkbox."""
    return st.checkbox(
        "🤖 **Auto-Process All Clients** (Recommended)", 
        value=True, 
        help="Automatically search and open all client records after downloading the JSON file"
    )


def render_export_button(auto_process: bool, automation_running: bool):
    """Render the main export button with appropriate text."""
    button_text = "⬇️ Export & Auto-Process All Clients" if auto_process else "⬇️ Export Client Notes Report"
    
    return st.button(
        button_text, 
        type="primary", 
        use_container_width=True, 
        disabled=automation_running
    )


def render_test_buttons(test_navigation_callback, preview_clients_callback):
    """Render test and preview buttons."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col3:
        test_clicked = st.button(
            "🧪 Test Navigation", 
            help="Test clicking on Clients menu to verify it works"
        )
    
    with col2:
        preview_clicked = st.button(
            "👀 Preview Clients", 
            help="Show which clients would be processed from the latest JSON file"
        )
    
    if test_clicked:
        test_navigation_callback()
    
    if preview_clicked:
        preview_clients_callback()


def render_client_selection(available_clients, search_callback):
    """Render client selection dropdown and search functionality."""
    if available_clients:
        st.info(f"📋 Found {len(available_clients)} clients from exported data")
        
        # Client selection dropdown
        selected_client = st.selectbox(
            "Select a client to search:",
            options=[""] + available_clients,
            help="Choose a client from the exported Client Notes data"
        )
        
        if selected_client and st.button("🔍 Search and Open Client Details", use_container_width=True):
            search_callback(selected_client)
    else:
        st.warning("📭 No clients found. Please export Client Notes data first.")


def display_export_success(file_path: Path, file_type: str):
    """Display export success information."""
    file_size_kb = max(1, file_path.stat().st_size // 1024)
    
    st.success(f"✅ Export Complete!")
    st.info(f"📁 **{file_type} file saved to:** `./downloads/{file_path.name}`")
    
    if file_type == "JSON":
        st.write("🔄 **Auto-converted:** Excel → JSON")
    
    st.write(f"📊 **File Size:** {file_size_kb} KB | **Records Ready for Processing**")


def display_processing_results(success_count: int, total_clients: int, processed_clients: list, failed_clients: list):
    """Display client processing results."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Successfully Processed", f"{success_count}/{total_clients}")
    with col2:
        st.metric("❌ Failed", len(failed_clients))
    with col3:
        st.metric("📋 Total Available", total_clients)
    
    if processed_clients:
        st.write("**Successfully Processed Clients:**")
        for client in processed_clients:
            st.write(f"✅ {client}")
    
    if failed_clients:
        st.write("**Failed Clients:**")
        for client in failed_clients:
            st.write(f"❌ {client}")


def display_client_data(client_name: str, extracted_data: dict):
    """Display extracted client data in an expandable format."""
    with st.expander(f"📊 Data for {client_name}", expanded=False):
        # Contact Information
        st.write("**📞 Contact Information:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"  • **Phone 1:** {extracted_data.get('phone_1', 'N/A')}")
            st.write(f"  • **Phone 2:** {extracted_data.get('phone_2', 'N/A')}")
            st.write(f"  • **Referral #:** {extracted_data.get('referral_number', 'N/A')}")
        with col2:
            st.write(f"  • **Med Record #:** {extracted_data.get('med_record', 'N/A')}")
            st.write(f"  • **Case Manager:** {extracted_data.get('case_manager', 'N/A')}")
        
        st.write("---")
        
        # Address Information
        st.write("**🏠 Address Information:**")
        address_line_1 = extracted_data.get('address_1', 'N/A')
        address_line_2 = extracted_data.get('address_2', '')
        city = extracted_data.get('city', 'N/A')
        state = extracted_data.get('state', 'N/A')
        zip_code = extracted_data.get('zip', 'N/A')
        county = extracted_data.get('county', 'N/A')
        
        st.write(f"  • **Address 1:** {address_line_1}")
        if address_line_2:
            st.write(f"  • **Address 2:** {address_line_2}")
        st.write(f"  • **City:** {city}")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            st.write(f"  • **State:** {state}")
        with col4:
            st.write(f"  • **Zip:** {zip_code}")
        with col5:
            st.write(f"  • **County:** {county}")
        
        st.write("---")
        
        # Service Dates
        st.write("**� Service Dates:**")
        col6, col7 = st.columns(2)
        with col6:
            st.write(f"  • **Service Start:** {extracted_data.get('service_start', 'N/A')}")
            st.write(f"  • **Inquiry Date:** {extracted_data.get('inquiry_date', 'N/A')}")
        with col7:
            st.write(f"  • **Service End:** {extracted_data.get('service_end', 'N/A')}")
            st.write(f"  • **Assessment:** {extracted_data.get('assessment', 'N/A')}")


def display_file_details(file_path: Path, start_str: str, end_str: str, file_type: str, sample_data=None):
    """Display detailed file information in an expandable section."""
    file_size_kb = max(1, file_path.stat().st_size // 1024)
    
    with st.expander("📊 Detailed Information"):
        st.write(f"**📄 File Name:** {file_path.name}")
        st.write(f"**📏 File Size:** {file_size_kb} KB")
        st.write(f"**📅 Date Range:** {start_str} → {end_str}")
        st.write(f"**📁 Location:** `./downloads/{file_path.name}`")
        st.write(f"**🗂️ Previous files moved to:** `./historic_outputs/`")
        
        if file_type == "JSON":
            st.write("**🔄 Conversion Status:** ✅ Excel → JSON completed")
            st.write("**📋 Columns:** All 9 required columns extracted")
            st.write("**🎯 Ready for:** Data processing and analysis")
            
            if sample_data:
                st.write(f"**📊 Total Records:** {len(sample_data)}")
                st.write("**📋 Sample Data (first 2 records):**")
                for i, record in enumerate(sample_data[:2]):
                    with st.container():
                        st.json(record, expanded=False)
                
                if len(sample_data) > 2:
                    st.caption(f"... and {len(sample_data) - 2} more records")


def display_preview_clients(clients_data: list):
    """Display preview of clients that would be processed."""
    if clients_data:
        st.success(f"Found {len(clients_data)} unique clients:")
        
        # Show first 10 clients in a nice format
        for i, client in enumerate(clients_data[:10], 1):
            st.write(f"{i}. **{client['full_name']}**")
            
            # Show search term that will be used
            search_last_name = client.get('original_last_name', client['last_name'])
            search_term = f"{search_last_name} {client['first_name']}"
            st.caption(f"   🔍 Search term: **{search_term}**")
            
            if client.get('original_last_name') != client['last_name']:
                st.caption(f"   ↳ Display name cleaned from: {client['original_last_name']}, {client['first_name']}")
        
        if len(clients_data) > 10:
            st.write(f"... and {len(clients_data) - 10} more clients")
    else:
        st.warning("No valid clients found in the latest JSON file")


def show_processing_status(current: int, total: int, client_name: str):
    """Show current processing status."""
    progress = current / total
    progress_bar = st.progress(progress)
    status_text = st.empty()
    status_text.text(f"Processing {current}/{total}: {client_name}")
    return progress_bar, status_text


def clear_processing_status(progress_bar, status_text):
    """Clear processing status indicators."""
    progress_bar.empty()
    status_text.empty()


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "driver" not in st.session_state:
        st.session_state.driver = None
    if "client_notes_value" not in st.session_state:
        st.session_state.client_notes_value = None
    if "client_notes_text" not in st.session_state:
        st.session_state.client_notes_text = None
    if "automation_running" not in st.session_state:
        st.session_state.automation_running = False
