"""
Main Streamlit application for Client Notes Automation.
Entry point that coordinates all modules and handles the UI workflow.
"""

import json
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Import our custom modules
from config import MAX_CLIENTS_PER_BATCH
from ui_components import (
    setup_streamlit_page, render_sidebar, render_connection_buttons,
    render_folder_metrics, render_date_range_selector, render_automation_checkbox,
    render_export_button, display_export_success, display_processing_results, 
    display_client_data, display_file_details, show_processing_status,
    clear_processing_status, initialize_session_state
)
from selenium_helpers import build_driver
from data_processing import manage_output_folders, get_clients_from_json_file
from report_automation import login_and_open_report_writer, find_client_notes_report, export_single_report
from client_search import navigate_to_clients, process_client_with_personal_data


# Load environment variables
load_dotenv()

# Initialize Streamlit
setup_streamlit_page()
initialize_session_state()

# Render sidebar and get settings
agency_id, email, password, headless, slow_step_delay = render_sidebar()

# Connection management functions
def connect_and_load():
    """Connect to browser and load reports."""
    # Manage output folders
    downloads_folder, historic_folder = manage_output_folders()
    
    # Use temporary directory for browser downloads
    st.session_state.download_dir = Path(tempfile.mkdtemp(prefix="dl_"))
    st.session_state.managed_downloads_folder = downloads_folder
    st.session_state.historic_folder = historic_folder
    
    driver = build_driver(st.session_state.download_dir, headless)
    try:
        if not (agency_id and email and password):
            raise ValueError("Please enter Agency ID, Email, and Password in the sidebar.")
        
        with st.status("Connecting to Generations...") as status:
            status.update(label="Logging in...")
            login_and_open_report_writer(driver, agency_id.strip(), email.strip(), password)
            
            status.update(label="Loading reports...")
            time.sleep(3)
            
            status.update(label="Finding Client Notes report...")
            client_notes_value, client_notes_text = find_client_notes_report(driver)
            
            status.update(label="Connected!", state="complete")
        
        st.session_state.driver = driver
        st.session_state.client_notes_value = client_notes_value
        st.session_state.client_notes_text = client_notes_text
        st.success(f"✅ Connected. Found report: **{client_notes_text}**")
        
    except Exception as e:
        try:
            driver.quit()
        except Exception:
            pass
        st.session_state.driver = None
        st.session_state.client_notes_value = None
        st.session_state.client_notes_text = None
        st.error(f"❌ Failed to connect or find Client Notes report: {e}")
        
        # Show debug info if running in non-headless mode
        if not headless:
            with st.expander("🔍 Debug Information"):
                st.write("**Current Page Title:**", getattr(driver, 'title', 'N/A') if 'driver' in locals() else 'Browser not available')
                st.write("**Current URL:**", getattr(driver, 'current_url', 'N/A') if 'driver' in locals() else 'Browser not available')


def disconnect():
    """Disconnect from browser and clean up."""
    if st.session_state.driver:
        try:
            st.session_state.driver.quit()
        except Exception:
            pass
    st.session_state.driver = None
    st.session_state.client_notes_value = None
    st.session_state.client_notes_text = None
    st.session_state.download_dir = None
    st.info("Disconnected and cleaned up.")


def refresh_page_twice_and_prepare(driver):
    """Refresh the page twice as required after export completion."""
    print("\n🔄 Refreshing page twice to prepare for client navigation...")
    
    try:
        # First refresh
        print("🔄 First page refresh...")
        driver.refresh()
        from selenium_helpers import wait_document_ready
        wait_document_ready(driver)
        time.sleep(3)
        
        # Second refresh  
        print("🔄 Second page refresh...")
        driver.refresh()
        wait_document_ready(driver)
        time.sleep(3)
        
        print("✅ Page refreshes completed, ready for client navigation")
        return True
        
    except Exception as e:
        print(f"❌ Error during page refresh: {e}")
        return False


def process_all_clients_automatically(driver, json_file_path: Path):
    """Automatically process all clients from the downloaded JSON file."""
    print("\n🔍 Starting automated client processing...")
    
    # First, refresh the page twice as required
    if not refresh_page_twice_and_prepare(driver):
        print("❌ Failed to refresh page, aborting client processing")
        st.error("❌ Failed to refresh page properly")
        return False
    
    # Extract clients from the JSON file
    clients = get_clients_from_json_file(json_file_path)
    
    if not clients:
        print("❌ No valid clients found in JSON file")
        st.error("❌ No valid clients found in JSON file")
        return False
    
    print(f"📋 Found {len(clients)} unique clients to process")
    
    # Limit the number of clients to process
    max_clients = min(len(clients), MAX_CLIENTS_PER_BATCH)
    clients_to_process = clients[:max_clients]
    
    if len(clients) > max_clients:
        st.warning(f"⚠️ Processing first {max_clients} clients out of {len(clients)} total. You can run again to process more.")
    
    # Display progress in Streamlit
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_clients = []
    processed_clients = []
    
    # Store the original tab handle
    try:
        original_tab = driver.current_window_handle
    except Exception as e:
        print(f"❌ Could not get current window handle: {e}")
        st.error("❌ Browser window issue. Please refresh and try again.")
        return False
    
    for i, client in enumerate(clients_to_process, 1):
        # Update progress
        progress = i / len(clients_to_process)
        progress_bar.progress(progress)
        status_text.text(f"Processing {i}/{len(clients_to_process)}: {client['full_name']}")
        
        print(f"\n🔍 Processing client {i}/{len(clients_to_process)}: {client['full_name']}")
        
        try:
            # Make sure we're back to the original tab before each search
            try:
                driver.switch_to.window(original_tab)
            except Exception as e:
                print(f"⚠️ Could not switch to original tab: {e}")
                if driver.window_handles:
                    driver.switch_to.window(driver.window_handles[0])
                    original_tab = driver.current_window_handle
                else:
                    raise Exception("No valid browser windows available")
            
            # Process client with personal data extraction
            extracted_data = process_client_with_personal_data(
                driver=driver,
                client_name=client['full_name'],
                last_name=client['last_name'],
                first_name=client['first_name'],
                original_last_name=client.get('original_last_name')
            )
            
            if extracted_data:
                success_count += 1
                processed_clients.append(client['full_name'])
                print(f"✅ Successfully processed: {client['full_name']}")
                
                # Save extracted data to JSON file
                from data_processing import update_json_with_personal_data
                update_json_with_personal_data(json_file_path, client['full_name'], extracted_data)
                
                # Display extracted data in Streamlit
                display_client_data(client['full_name'], extracted_data)
                
                # Brief pause before next client
                time.sleep(2)
                
                # Ensure we're back to original tab for next iteration
                try:
                    if driver.current_window_handle != original_tab and original_tab in driver.window_handles:
                        driver.switch_to.window(original_tab)
                        print(f"↩️ Returned to original tab for next client")
                except Exception as e:
                    print(f"⚠️ Could not return to original tab: {e}")
                    if driver.window_handles:
                        original_tab = driver.window_handles[0]
                        driver.switch_to.window(original_tab)
                
            else:
                failed_clients.append(client['full_name'])
                print(f"❌ Failed to open: {client['full_name']}")
                
                # Ensure we're back to original tab even on failure
                try:
                    if original_tab in driver.window_handles:
                        driver.switch_to.window(original_tab)
                except Exception:
                    if driver.window_handles:
                        original_tab = driver.window_handles[0]
                        driver.switch_to.window(original_tab)
                
        except Exception as e:
            failed_clients.append(client['full_name'])
            print(f"❌ Error processing {client['full_name']}: {e}")
            
            # Ensure we're back to original tab even on error
            try:
                driver.switch_to.window(original_tab)
            except Exception:
                pass
            
        # Brief pause between clients
        time.sleep(1)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show final summary
    print(f"\n📊 Processing Summary:")
    print(f"✅ Successfully processed: {success_count}/{len(clients_to_process)} clients")
    
    # Display results in Streamlit
    display_processing_results(success_count, len(clients_to_process), processed_clients, failed_clients)
    
    return success_count > 0


# Main UI Layout
render_connection_buttons(connect_and_load, disconnect)
st.divider()

# Show folder management status
render_folder_metrics(
    getattr(st.session_state, 'managed_downloads_folder', None),
    getattr(st.session_state, 'historic_folder', None)
)

# Main application logic
if st.session_state.client_notes_value and st.session_state.client_notes_text:
    st.info(f"🎯 **Report:** {st.session_state.client_notes_text}")
    
    # Date range selection
    start_dt, end_dt = render_date_range_selector()
    to_mmddyyyy = lambda d: d.strftime("%m/%d/%Y")
    start_str, end_str = to_mmddyyyy(start_dt), to_mmddyyyy(end_dt)
    
    st.write(f"**Date Range:** {start_str} → {end_str}")

    # Automation control
    auto_process = render_automation_checkbox()

    if st.session_state.driver:
        if render_export_button(auto_process, st.session_state.automation_running):
            # Set automation flag
            st.session_state.automation_running = True
            
            try:
                with st.spinner("📥 Exporting Client Notes report..."):
                    path = export_single_report(
                        driver=st.session_state.driver,
                        download_dir=st.session_state.download_dir,
                        option_value=st.session_state.client_notes_value,
                        option_text=st.session_state.client_notes_text,
                        start_str=start_str,
                        end_str=end_str
                    )
                    
                    if path and path.exists():
                        # Determine file type
                        file_type = "JSON" if path.suffix.lower() == '.json' else "Excel"
                        
                        # Show export success
                        display_export_success(path, file_type)
                        
                        # Show extraction complete message  
                        st.write("---")
                        st.success("✅ **Extraction Complete!**")
                        st.info(f"📁 **JSON saved to:** `./downloads/{path.name}`")
                        
                        # Automatically process all clients if enabled
                        if file_type == "JSON" and auto_process:
                            st.write("---")
                            st.write("🔍 **Searching for Clients...**")
                            st.info("📋 **Strategy:** Page refresh → Clients → Client List → Search → Personal Data → Extract info")
                            
                            with st.spinner("🤖 Preparing page and processing clients automatically..."):
                                try:
                                    success = process_all_clients_automatically(
                                        driver=st.session_state.driver,
                                        json_file_path=path
                                    )
                                    
                                    if success:
                                        st.success("✅ Automated client processing completed!")
                                        st.write("🎯 **Client data extracted successfully! Personal information displayed above.**")
                                        st.info("📋 **Extracted:** Phone numbers, service dates, inquiry date, and assessment date")
                                        
                                        # Automatically generate Excel file after JSON processing
                                        st.write("---")
                                        st.write("📊 **Generating Excel Report...**")
                                        with st.spinner("📈 Creating Excel file from JSON data..."):
                                            try:
                                                # Import and run the Excel generation
                                                import subprocess
                                                import sys
                                                
                                                # Run mapping2excel.py script
                                                result = subprocess.run([sys.executable, "mapping2excel.py"], 
                                                                      capture_output=True, text=True, cwd=".")
                                                
                                                if result.returncode == 0:
                                                    st.success("✅ **Excel file generated successfully!**")
                                                    
                                                    # Extract information from output
                                                    output_lines = result.stdout.split('\n')
                                                    excel_filename = None
                                                    records_processed = None
                                                    columns_count = None
                                                    
                                                    for line in output_lines:
                                                        if 'Filename:' in line:
                                                            excel_filename = line.split('Filename:')[1].strip()
                                                        elif 'Total records processed:' in line:
                                                            records_processed = line.split(':')[1].strip()
                                                        elif 'Columns in template:' in line:
                                                            columns_count = line.split(':')[1].strip()
                                                    
                                                    # Display Excel file information
                                                    if excel_filename:
                                                        st.info(f"📄 **Excel Report:** `./downloads/{excel_filename}`")
                                                        
                                                    # Show processing statistics
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        if records_processed:
                                                            st.metric("Records Processed", records_processed)
                                                    with col2:
                                                        if columns_count:
                                                            st.metric("KP Template Columns", columns_count)
                                                    
                                                    st.success("🎯 **Complete!** JSON data has been converted to KP Excel format.")
                                                            
                                                else:
                                                    st.error(f"❌ Excel generation failed: {result.stderr}")
                                                    if result.stdout:
                                                        st.text(f"Output: {result.stdout}")
                                                    
                                            except Exception as excel_error:
                                                st.error(f"❌ Error generating Excel file: {excel_error}")
                                                
                                    else:
                                        st.warning("⚠️ Some issues occurred during client processing")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error during automated client processing: {e}")
                                    import traceback
                                    st.text(traceback.format_exc())
                        elif file_type == "JSON" and not auto_process:
                            st.info("ℹ️ **Automation disabled.** Enable automation to process clients automatically.")
                        
                        # Display detailed file information
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                sample_data = json.load(f)
                        except Exception:
                            sample_data = None
                            
                        display_file_details(path, start_str, end_str, file_type, sample_data)
                        
                    else:
                        st.error("❌ Export finished but file was not found.")
                        
            except Exception as e:
                st.error(f"❌ Export failed: {e}")
            finally:
                # Reset automation flag
                st.session_state.automation_running = False
    
    else:
        st.warning("⚠️ Browser connection lost. Please reconnect.")
        
elif st.session_state.driver:
    st.error("❌ Client Notes report not found. Please disconnect and try again.")
else:
    st.info("👆 Enter credentials in the sidebar, then click **Connect & Load Reports**.")
