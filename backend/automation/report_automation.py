"""
Report automation functions for Generations system.
Handles login, report generation, and export processes.
"""

import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from automation.config import (
    LOGIN_URL, REPORTS_MENU_ID, REPORT_WRITER_XPATH, DROPDOWN_ID, DISPLAY_BTN_ID,
    DATE_PANEL_ID, START_DATE_ID, END_DATE_ID, DATE_OK_BTN_ID, EXPORT_BTN_ID,
    CLIENT_STATUS_DROPDOWN_ID, PAYOR_DROPDOWN_ID, COLUMN_CHOOSER_BTN_ID,
    TARGET_REPORT_NAME, REQUIRED_COLUMNS, EXPORT_MAX_RETRIES, COLUMN_MAX_RETRIES
)
from automation.selenium_helpers import (
    wait_document_ready, try_switch_to_panel_context, set_input_value_by_id_js,
    find_element_in_any_frame, wait_invisibility_in_any_frame, handle_warning_popups,
    retry_on_stale_element, safe_find_and_click, safe_select_dropdown, refresh_page_context,
    wait_for_downloads
)
from automation.data_processing import convert_excel_to_json, sanitize_filename, unique_path


def login_and_open_report_writer(driver, agency_id: str, email: str, password: str):
    """Login to Generations system and open Report Writer."""
    driver.get(LOGIN_URL)
    wait_document_ready(driver)

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtAgencyID"))).send_keys(agency_id)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtLogin"))).send_keys(email)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtPassword"))).send_keys(password)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "btnUserLogin"))).click()
    wait_document_ready(driver)

    reports_menu = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, REPORTS_MENU_ID)))
    driver.execute_script("arguments[0].click();", reports_menu)

    report_writer_link = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, REPORT_WRITER_XPATH)))
    old_handles = set(driver.window_handles)
    driver.execute_script("arguments[0].click();", report_writer_link)

    # Switch to new tab/window if it opens
    try:
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > len(old_handles))
        new_handle = next(iter(set(driver.window_handles) - old_handles))
        driver.switch_to.window(new_handle)
    except TimeoutException:
        pass

    wait_document_ready(driver)
    return driver


def fetch_report_options(driver):
    """Fetch available report options from dropdown."""
    try:
        dropdown_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, DROPDOWN_ID)))
    except TimeoutException:
        # Try in iframes
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                dropdown_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, DROPDOWN_ID)))
                break
            except TimeoutException:
                driver.switch_to.default_content()
                continue
        else:
            raise TimeoutException(f"Could not find dropdown with ID: {DROPDOWN_ID}")
    
    time.sleep(1)
    dropdown = Select(dropdown_element)
    
    options = []
    for opt in dropdown.options:
        value = opt.get_attribute("value") or ""
        text = (opt.text or "").strip()
        if text:
            options.append((value, text))
    
    return options


def find_client_notes_report(driver):
    """Find the Client Notes report in the dropdown options."""
    options = fetch_report_options(driver)
    for value, text in options:
        if TARGET_REPORT_NAME.lower() in text.lower():
            return value, text
    raise ValueError(f"Report '{TARGET_REPORT_NAME}' not found in dropdown options")


def export_single_report(driver, download_dir: Path, option_value: str, option_text: str, start_str: str, end_str: str) -> Path | None:
    """Select Client Notes report, configure settings, set date range, select columns, and export."""
    
    def _complete_export():
        return _do_export_steps(driver, download_dir, option_value, option_text, start_str, end_str)
    
    # Use retry wrapper with longer delays for stale element issues
    return retry_on_stale_element(_complete_export, max_retries=EXPORT_MAX_RETRIES, delay=3)


def _do_export_steps(driver, download_dir: Path, option_value: str, option_text: str, start_str: str, end_str: str) -> Path | None:
    """Internal function that performs the actual export steps."""
    print("Step 1: Selecting Client Notes report...")
    refresh_page_context(driver)
    safe_select_dropdown(driver, DROPDOWN_ID, option_value)
    time.sleep(2)

    print("Step 2: First Display Report click...")
    refresh_page_context(driver)
    safe_find_and_click(driver, (By.ID, DISPLAY_BTN_ID))
    time.sleep(2)

    print("Step 3: Setting dates in calendar...")
    try:
        try_switch_to_panel_context(driver, DATE_PANEL_ID)
        set_input_value_by_id_js(driver, START_DATE_ID, start_str)
        time.sleep(0.3)
        set_input_value_by_id_js(driver, END_DATE_ID, end_str)
        time.sleep(0.3)
        safe_find_and_click(driver, (By.ID, DATE_OK_BTN_ID))
        driver.switch_to.default_content()
        wait_invisibility_in_any_frame(driver, (By.ID, DATE_PANEL_ID), total_timeout=15)
    except TimeoutException:
        driver.switch_to.default_content()
    
    time.sleep(2)

    print("Step 4: Selecting Status...")
    _handle_status_dropdown(driver)
    time.sleep(1)

    print("Step 5: Handling Payor dropdown...")
    _handle_payor_dropdown(driver)

    print("Step 6: Display Report after Status/Payor selection...")
    _handle_second_display_click(driver)

    print("Step 7: Handling Column Chooser...")
    _handle_column_selection(driver)

    print("Step 8: Final Display Report click...")
    _handle_final_display_click(driver)

    print("Step 9: Finding and clicking export button...")
    downloaded_file = _handle_export_and_download(driver, download_dir, option_text, start_str, end_str)
    
    return downloaded_file


def _handle_status_dropdown(driver):
    """Handle the Status dropdown selection."""
    try:
        safe_select_dropdown(driver, CLIENT_STATUS_DROPDOWN_ID, "All")
    except TimeoutException:
        print("Status dropdown not found with ID, trying XPath...")
        try:
            def _select_status_xpath():
                status_dropdown = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'ddlClientType')]"))
                )
                Select(status_dropdown).select_by_value("All")
                return True
            retry_on_stale_element(_select_status_xpath)
        except TimeoutException:
            print("Status dropdown not found at all, continuing...")


def _handle_payor_dropdown(driver):
    """Handle the Payor dropdown selection."""
    try:
        payor_dropdown = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, PAYOR_DROPDOWN_ID)))
        payor_select = Select(payor_dropdown)
        for option in payor_select.options:
            if "all" in option.text.lower():
                payor_select.select_by_visible_text(option.text)
                break
        time.sleep(0.3)
        handle_warning_popups(driver)
    except TimeoutException:
        try:
            payor_dropdown = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Payor')]/following-sibling::td//select"))
            )
            payor_select = Select(payor_dropdown)
            for option in payor_select.options:
                if "all" in option.text.lower():
                    payor_select.select_by_visible_text(option.text)
                    break
            time.sleep(0.3)
            handle_warning_popups(driver)
        except TimeoutException:
            pass


def _handle_second_display_click(driver):
    """Handle the second Display Report click and calendar popup."""
    try:
        safe_find_and_click(driver, (By.ID, DISPLAY_BTN_ID))
        time.sleep(0.5)
        handle_warning_popups(driver)
        
        # Handle calendar popup (dates already set from first calendar, just click OK)
        try:
            try_switch_to_panel_context(driver, DATE_PANEL_ID)
            time.sleep(0.3)
            safe_find_and_click(driver, (By.ID, DATE_OK_BTN_ID))
            time.sleep(0.3)
            driver.switch_to.default_content()
            handle_warning_popups(driver)
            wait_invisibility_in_any_frame(driver, (By.ID, DATE_PANEL_ID), total_timeout=15)
        except TimeoutException:
            driver.switch_to.default_content()
        
        wait_document_ready(driver)
    except TimeoutException:
        pass


def _handle_column_selection(driver):
    """Handle the Column Chooser functionality."""
    try:
        # Find and click Column Chooser button
        column_chooser_clicked = _find_and_click_column_chooser(driver)
        
        if not column_chooser_clicked:
            raise TimeoutException("Column Chooser button not found after extensive search")
            
        time.sleep(1)

        # Remove all columns first
        remove_all_clicked = _click_remove_all_checkbox(driver)
        
        if not remove_all_clicked:
            _manually_uncheck_columns(driver)
        
        time.sleep(2)

        # Select required columns
        columns_selected = _select_required_columns(driver)
        print(f"\nColumn Selection Summary: {columns_selected} out of {len(REQUIRED_COLUMNS)} required columns")

        # Click OK to apply selection
        _click_column_chooser_ok(driver)
        
        driver.switch_to.default_content()
        time.sleep(0.5)
        wait_document_ready(driver)
        
    except TimeoutException:
        pass


def _find_and_click_column_chooser(driver):
    """Find and click the Column Chooser button."""
    try:
        safe_find_and_click(driver, (By.ID, COLUMN_CHOOSER_BTN_ID), timeout=5)
        return True
    except TimeoutException:
        # Try alternative selectors
        column_chooser_patterns = [
            "//img[contains(@id, 'ColumnChooser')]",
            "//input[contains(@id, 'ColumnChooser')]", 
            "//a[contains(@id, 'ColumnChooser')]",
            "//img[contains(@title, 'Column') or contains(@alt, 'Column')]",
            "//img[contains(@src, 'column') or contains(@src, 'Column')]",
            "//a[contains(text(), 'Column') or contains(@title, 'Column')]",
            "//input[@value='Column Chooser']",
            "//button[contains(text(), 'Column')]"
        ]
        
        for pattern in column_chooser_patterns:
            try:
                _, column_chooser_btn = find_element_in_any_frame(driver, (By.XPATH, pattern), condition="clickable", total_timeout=3)
                driver.execute_script("arguments[0].click();", column_chooser_btn)
                return True
            except TimeoutException:
                continue
    
    return False


def _click_remove_all_checkbox(driver):
    """Click the Remove All checkbox to clear all column selections."""
    max_retries = COLUMN_MAX_RETRIES
    
    for retry_attempt in range(max_retries):
        try:
            print(f"Remove All attempt {retry_attempt + 1}/{max_retries}")
            
            # Wait for Column Chooser iframe
            try:
                driver.switch_to.default_content()
                iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "frameMainArea"))
                )
                driver.switch_to.frame(iframe)
                
                # Look for Remove All checkbox
                remove_all_checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cphPopup_ColumnChooserControl_chkRemoveAll"))
                )
                
                driver.execute_script("arguments[0].scrollIntoView(true);", remove_all_checkbox)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", remove_all_checkbox)
                time.sleep(1)
                print("Remove All checkbox clicked successfully")
                return True
                
            except TimeoutException:
                # Fallback to find_element_in_any_frame
                frame_name, remove_all_checkbox = find_element_in_any_frame(
                    driver, 
                    (By.ID, "ctl00_cphPopup_ColumnChooserControl_chkRemoveAll"), 
                    condition="clickable", 
                    total_timeout=10
                )
                driver.execute_script("arguments[0].click();", remove_all_checkbox)
                print("Remove All checkbox clicked successfully via fallback")
                return True
                
        except (Exception) as e:
            print(f"Remove All attempt {retry_attempt + 1} failed: {e}")
            if retry_attempt < max_retries - 1:
                time.sleep(2)
                driver.switch_to.default_content()
    
    return False


def _manually_uncheck_columns(driver):
    """Manually uncheck all selected checkboxes if Remove All failed."""
    print("Remove All failed - manually unchecking all checkboxes...")
    
    unchecked_count = 0
    try:
        all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and contains(@name, 'chkSelectColumn')]")
        for checkbox in all_checkboxes:
            try:
                if checkbox.is_displayed() and checkbox.is_enabled() and checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    unchecked_count += 1
                    time.sleep(0.1)
            except Exception:
                continue
    except Exception:
        pass
    
    print(f"Manually unchecked {unchecked_count} checkboxes")


def _select_required_columns(driver):
    """Select only the required columns for the report."""
    columns_selected = 0
    
    for column_name in REQUIRED_COLUMNS:
        print(f"Looking for column: {column_name}")
        
        xpath_patterns = [
            f"//span[@class='columnselection'][@title='{column_name}']//input[@type='checkbox']",
            f"//label[text()='{column_name}']/..//input[@type='checkbox']",
            f"//tr[contains(., '{column_name}')]//input[@type='checkbox' and contains(@name, 'chkSelectColumn')]",
            f"//td[contains(., '{column_name}')]//input[@type='checkbox']"
        ]
        
        column_found = False
        max_retries = COLUMN_MAX_RETRIES
        
        for retry_attempt in range(max_retries):
            try:
                for i, xpath in enumerate(xpath_patterns):
                    try:
                        checkbox = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if not checkbox.is_selected():
                            driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                            time.sleep(0.2)
                            driver.execute_script("arguments[0].click();", checkbox)
                            print(f"✓ Selected: {column_name} (pattern {i+1})")
                        else:
                            print(f"✓ Already selected: {column_name}")
                        columns_selected += 1
                        time.sleep(0.2)
                        column_found = True
                        break
                    except TimeoutException:
                        continue
                
                if column_found:
                    break
                    
            except Exception as e:
                print(f"Column {column_name} retry {retry_attempt + 1} failed: {e}")
                if retry_attempt < max_retries - 1:
                    time.sleep(1)
        
        if not column_found:
            print(f"✗ Could not find: {column_name}")
    
    return columns_selected


def _click_column_chooser_ok(driver):
    """Click OK button in Column Chooser to apply selections."""
    max_retries = COLUMN_MAX_RETRIES
    
    for retry_attempt in range(max_retries):
        try:
            ok_patterns = [
                (By.XPATH, "//input[@value='OK']"),
                (By.XPATH, "//input[@value='Apply']"),
                (By.XPATH, "//button[contains(text(), 'OK')]"),
            ]
            
            for i, locator in enumerate(ok_patterns):
                try:
                    ok_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(locator))
                    driver.execute_script("arguments[0].click();", ok_btn)
                    print("OK button clicked successfully")
                    return True
                except TimeoutException:
                    continue
            
        except Exception as e:
            print(f"OK button attempt {retry_attempt + 1} failed: {e}")
            if retry_attempt < max_retries - 1:
                time.sleep(2)
    
    print("WARNING: Could not click OK button, proceeding anyway")
    return False


def _handle_final_display_click(driver):
    """Handle the final Display Report click."""
    try:
        safe_find_and_click(driver, (By.ID, DISPLAY_BTN_ID), timeout=8)
        time.sleep(0.5)
        handle_warning_popups(driver)
        
        # Handle final calendar popup
        try:
            try_switch_to_panel_context(driver, DATE_PANEL_ID)
            time.sleep(0.3)
            safe_find_and_click(driver, (By.ID, DATE_OK_BTN_ID))
            time.sleep(0.3)
            driver.switch_to.default_content()
            handle_warning_popups(driver)
            wait_invisibility_in_any_frame(driver, (By.ID, DATE_PANEL_ID), total_timeout=15)
        except TimeoutException:
            driver.switch_to.default_content()
        
        wait_document_ready(driver)
    except TimeoutException:
        pass


def _handle_export_and_download(driver, download_dir: Path, option_text: str, start_str: str, end_str: str):
    """Handle the export button click and download monitoring."""
    
    def _find_and_click_export():
        refresh_page_context(driver)
        time.sleep(2)
        
        frame_name, export_btn = find_element_in_any_frame(
            driver, (By.ID, EXPORT_BTN_ID), condition="clickable", total_timeout=20
        )
        print(f"Found export button in {frame_name}")
        
        # Record files before export
        before = {p.name for p in download_dir.glob("*") if not p.name.endswith(".crdownload")}
        
        # Click export button
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", export_btn)
            time.sleep(1)
            if export_btn.is_enabled() and export_btn.is_displayed():
                driver.execute_script("arguments[0].click();", export_btn)
                print("Export button clicked successfully")
                return True
            else:
                raise Exception("Export button not clickable")
        except Exception:
            # Re-find if stale
            frame_name, export_btn = find_element_in_any_frame(
                driver, (By.ID, EXPORT_BTN_ID), condition="clickable", total_timeout=10
            )
            driver.execute_script("arguments[0].click();", export_btn)
            print("Export button clicked successfully after re-find")
            return True
    
    # Click export with retries
    retry_on_stale_element(_find_and_click_export, max_retries=EXPORT_MAX_RETRIES, delay=4)

    # Monitor download completion
    print("Monitoring download completion...")
    
    before_files = {p.name for p in download_dir.glob("*") if not p.name.endswith(".crdownload")}
    
    start_wait_time = time.time()
    max_wait_time = 180
    check_interval = 3
    downloaded_file = None
    
    while time.time() - start_wait_time < max_wait_time:
        try:
            current_files = {p.name for p in download_dir.glob("*") if not p.name.endswith(".crdownload")}
            new_files = current_files - before_files
            
            if new_files:
                temp_files = list(download_dir.glob("*.crdownload"))
                if not temp_files:
                    new_file_name = list(new_files)[0]
                    downloaded_file = download_dir / new_file_name
                    
                    if downloaded_file.exists() and downloaded_file.stat().st_size > 0:
                        print(f"\n✅ Download completed: {downloaded_file.name} ({downloaded_file.stat().st_size} bytes)")
                        break
                else:
                    print(f"\n⏳ Download in progress... ({len(temp_files)} temporary files)")
            
            elapsed = time.time() - start_wait_time
            remaining = max_wait_time - elapsed
            print(".", end="", flush=True)
            if int(elapsed) % 15 == 0:
                print(f" ({int(remaining)}s remaining)")
            
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"\n⚠️ Error during download monitoring: {e}")
            time.sleep(check_interval)
    else:
        print(f"\n❌ Download timeout - no file appeared in {max_wait_time} seconds")
        current_files = list(download_dir.glob("*"))
        print(f"Current download directory contains: {[f.name for f in current_files]}")
        raise TimeoutException("Download did not complete in time.")
    
    if not downloaded_file:
        raise TimeoutException("No file found after export.")
    
    # Process the downloaded file
    latest = downloaded_file
    base_name = sanitize_filename(f"{option_text}_{start_str.replace('/', '-')}_{end_str.replace('/', '-')}")
    target = unique_path(download_dir / f"{base_name}{latest.suffix.lower()}")
    latest.rename(target)
    
    # Convert Excel to JSON and save to workspace downloads folder
    workspace_downloads = Path.cwd() / "downloads"
    workspace_downloads.mkdir(exist_ok=True)
    
    json_path = convert_excel_to_json(target, workspace_downloads)
    return json_path
