"""
Client search and personal data extraction functions.
Handles navigation to client records and data extraction.
"""

import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config import (
    CLIENTS_MENU_ID, CLIENT_LIST_LINK_ID, SEARCH_BOX_ID, SEARCH_BUTTON_ID,
    CLIENT_TYPE_DROPDOWN_ID, PERSONAL_DATA_TAB_ID, PERSONAL_DATA_FIELDS
)
from selenium_helpers import wait_document_ready, handle_warning_popups


def navigate_to_clients(driver):
    """Navigate to Clients → Client List."""
    print("🔍 Navigating to Clients → Client List...")
    
    # First, handle any existing alerts or popups
    try:
        handle_warning_popups(driver)
        print("✅ Cleared any existing alerts before navigation")
    except Exception:
        pass
    
    try:
        # Verify main menu is accessible
        main_menu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mnMianMenu"))
        )
        print(f"✅ Found main menu: {main_menu.tag_name} with class '{main_menu.get_attribute('class')}'")
        
        # Hover over Clients menu
        print(f"🎯 Hovering over Clients menu (ID: {CLIENTS_MENU_ID})")
        clients_menu = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, CLIENTS_MENU_ID))
        )
        print(f"✅ Found Clients menu: {clients_menu.tag_name}")
        
        # Hover to show submenu
        actions = ActionChains(driver)
        actions.move_to_element(clients_menu).perform()
        print("✅ Hovered over Clients menu to show submenu")
        time.sleep(1)
        
        # Look for Client List submenu option
        print(f"🎯 Looking for Client List submenu option...")
        
        # Store current window handles
        old_handles = set(driver.window_handles)
        print(f"📊 Current window handles before Client List click: {len(old_handles)}")
        
        # Try multiple selectors for Client List
        client_list_selectors = [
            (By.ID, CLIENT_LIST_LINK_ID),
            (By.XPATH, "//a[contains(text(), 'Client List')]"),
            (By.XPATH, "//a[contains(@href, 'client')]"),
            (By.CSS_SELECTOR, "a[href*='client']"),
        ]
        
        client_list_clicked = False
        for selector_type, selector in client_list_selectors:
            try:
                client_list_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((selector_type, selector))
                )
                print(f"✅ Found Client List link using {selector_type}: {selector}")
                
                # Click the Client List link
                driver.execute_script("arguments[0].click();", client_list_link)
                print("✅ Clicked Client List link")
                
                # Handle potential alert about page already being open
                try:
                    print("🔍 Checking for alerts after Client List click...")
                    alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                    alert_text = alert.text
                    print(f"⚠️ Alert detected: {alert_text}")
                    
                    if "already opened" in alert_text.lower():
                        print("🔧 Handling 'already opened' alert...")
                        alert.accept()
                        print("✅ Alert dismissed")
                        
                        # Close any existing Client List tabs
                        print("🗂️ Closing existing Client List tabs...")
                        _close_existing_client_tabs(driver)
                        
                        # Try clicking the Client List link again
                        print("🔄 Retrying Client List navigation...")
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", client_list_link)
                        print("✅ Clicked Client List link (retry)")
                    else:
                        alert.accept()
                        print("✅ Unknown alert dismissed")
                        
                except TimeoutException:
                    print("✅ No alerts detected after Client List click")
                except Exception as alert_error:
                    print(f"⚠️ Error handling alert: {alert_error}")
                
                client_list_clicked = True
                break
                
            except TimeoutException:
                print(f"⚠️ Client List not found with {selector_type}: {selector}")
                continue
        
        if not client_list_clicked:
            print("❌ Could not find Client List submenu option")
            return False
        
        # Wait for new tab/window and switch to it
        try:
            print("⏳ Waiting for Client List tab to open...")
            WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > len(old_handles))
            new_handles = set(driver.window_handles) - old_handles
            new_handle = next(iter(new_handles))
            driver.switch_to.window(new_handle)
            print(f"✅ Switched to Client List tab (total tabs: {len(driver.window_handles)})")
        except TimeoutException:
            print("⚠️ No new tab opened for Client List, continuing in current tab")
        
        # Wait for Client List page to be ready with alert handling
        try:
            print("⏳ Waiting for page to be ready...")
            wait_document_ready(driver)
            print("✅ Page ready")
        except Exception as e:
            print(f"⚠️ Error waiting for page ready: {e}")
            # Try to handle any remaining alerts
            try:
                handle_warning_popups(driver)
                print("✅ Handled additional popups after page load")
            except Exception:
                pass
        
        time.sleep(3)
        
        # Verify we're on the Client List page
        try:
            current_url = driver.current_url
            page_title = driver.title
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page Title: {page_title}")
            
            if "client" in current_url.lower() or "client" in page_title.lower():
                print("✅ Successfully navigated to Client List page")
                return True
        except Exception:
            pass
            
        print("✅ Navigation completed - ready for client search")
        return True
        
    except Exception as e:
        print(f"❌ Error navigating to Clients → Client List: {e}")
        import traceback
        traceback.print_exc()
        return False


def search_client(driver, last_name, first_name):
    """Search for a client using LastName FirstName format."""
    search_term = f"{last_name} {first_name}"
    print(f"🔍 Searching for client: {search_term}")
    
    try:
        # Find search box and enter search term first
        print(f"🎯 Looking for search box with ID: {SEARCH_BOX_ID}")
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, SEARCH_BOX_ID))
        )
        print(f"✅ Found search box: {search_box.tag_name}")
        
        # Clear and enter search term
        search_box.clear()
        search_box.send_keys(search_term)
        print(f"✅ Entered search term: '{search_term}'")
        time.sleep(0.5)
        
        # Set client type to "All Clients" AFTER entering search term
        print(f"🔧 Setting client type to 'All Clients'...")
        try:
            client_type_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, CLIENT_TYPE_DROPDOWN_ID))
            )
            select = Select(client_type_dropdown)
            select.select_by_value("All")
            print("✅ Set client type to 'All Clients'")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Could not set client type dropdown: {e}")
            # Continue with search anyway
        
        # Click search button
        print(f"🎯 Looking for search button with ID: {SEARCH_BUTTON_ID}")
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, SEARCH_BUTTON_ID))
        )
        print(f"✅ Found search button: {search_button.tag_name}")
        
        driver.execute_script("arguments[0].click();", search_button)
        print("✅ Clicked search button")
        
        # Wait for search results
        print("⏳ Waiting for search results...")
        wait_document_ready(driver)
        time.sleep(3)
        
        print(f"✅ Search completed for: {search_term}")
        return search_term
        
    except Exception as e:
        print(f"❌ Error during client search: {e}")
        # Try alternative search methods
        try:
            print("🔄 Trying alternative search box selectors...")
            alternative_selectors = [
                "input[type='text'][name*='search']",
                "input[type='search']",
                "#txtClientSearch",
                "input[placeholder*='search' i]"
            ]
            
            for selector in alternative_selectors:
                try:
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                    search_box.clear()
                    search_box.send_keys(search_term)
                    search_box.send_keys(Keys.ENTER)
                    print(f"✅ Used alternative selector: {selector}")
                    time.sleep(2)
                    return search_term
                except:
                    continue
                    
        except Exception as e2:
            print(f"❌ All search methods failed: {e2}")
        
        raise e


def find_and_click_client(driver, last_name, first_name):
    """Find the client in search results and click on their name link."""
    print(f"Looking for client link: {last_name} {first_name}")
    
    try:
        # Wait for the client list panel to load
        wait = WebDriverWait(driver, 15)
        
        # Wait for client results panel
        client_list_panel = wait.until(EC.presence_of_element_located((By.ID, "ctl00_MainContent_pnlClientList")))
        print("✅ Client list panel found")
        
        # Multiple selectors to find client links
        client_link_selectors = [
            "//div[@id='ctl00_MainContent_pnlClientList']//a[contains(@id, 'ClientName')]",
            "//table[@id='NewTable']//a[contains(@onclick, 'fnShowClientDetails')]",
            "//div[@id='ctl00_MainContent_pnlClientList']//a[@title]",
            "//table[@class='dynamic-div dtlstTable fixed-tbl DragTable']//a"
        ]
        
        # Search for the specific client
        target_client = None
        search_patterns = [
            f"{last_name} ECM {first_name}",
            f"{last_name} {first_name}",
            f"{first_name} {last_name}",
            f"{last_name.lower()} ecm {first_name.lower()}",
            f"{last_name.lower()} {first_name.lower()}",
        ]
        
        for selector in client_link_selectors:
            try:
                client_links = driver.find_elements(By.XPATH, selector)
                print(f"🔍 Found {len(client_links)} client links with selector: {selector}")
                
                for link in client_links:
                    link_text = link.get_attribute("title") or link.text or ""
                    link_text_clean = link_text.strip()
                    client_id = link.get_attribute("clientid") or ""
                    
                    print(f"   📋 Checking client: '{link_text_clean}' (ID: {client_id})")
                    
                    for pattern in search_patterns:
                        if pattern.lower() in link_text_clean.lower():
                            target_client = link
                            print(f"✅ Found matching client: {link_text_clean}")
                            break
                    
                    if target_client:
                        break
                
                if target_client:
                    break
                    
            except Exception as selector_error:
                print(f"⚠️ Selector failed: {selector} - {str(selector_error)}")
                continue
        
        if target_client:
            # Store current window handles before clicking
            old_handles = set(driver.window_handles)
            
            # Scroll to element and click
            driver.execute_script("arguments[0].scrollIntoView(true);", target_client)
            time.sleep(1)
            
            # Get client details
            client_title = target_client.get_attribute("title") or target_client.text
            client_id = target_client.get_attribute("clientid")
            
            print(f"🎯 Found target client element:")
            print(f"   📋 Title: {client_title}")
            print(f"   🆔 Client ID: {client_id}")
            
            # Try multiple click methods
            click_successful = False
            
            # Method 1: JavaScript click
            try:
                print("🔄 Attempting JavaScript click...")
                driver.execute_script("arguments[0].click();", target_client)
                time.sleep(2)
                click_successful = True
                print("✅ JavaScript click executed")
            except Exception as js_error:
                print(f"❌ JavaScript click failed: {js_error}")
            
            # Method 2: Direct click if JavaScript failed
            if not click_successful:
                try:
                    print("🔄 Attempting direct click...")
                    target_client.click()
                    time.sleep(2)
                    click_successful = True
                    print("✅ Direct click executed")
                except Exception as direct_error:
                    print(f"❌ Direct click failed: {direct_error}")
            
            if not click_successful:
                print("❌ All click methods failed!")
                return False
            
            # Check for navigation or new tab
            current_handles = set(driver.window_handles)
            
            # Wait for either new tab or page change
            try:
                if len(current_handles) > len(old_handles):
                    print("🔄 New tab detected, switching...")
                    new_handle = next(iter(current_handles - old_handles))
                    driver.switch_to.window(new_handle)
                    print("✅ Switched to client details tab")
                    wait_document_ready(driver)
                    return True
                else:
                    print("🔄 Checking for page change in current tab...")
                    wait_document_ready(driver)
                    
                    # Look for client details indicators
                    client_detail_indicators = [
                        "//td[@id='ctl00_MainContent_tdPersonalData']",
                        "//div[contains(@class, 'client-details')]",
                        "//form[@id='aspnetForm']//div[contains(text(), 'Client')]"
                    ]
                    
                    for indicator in client_detail_indicators:
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, indicator))
                            )
                            print("✅ Client details page loaded in current tab")
                            return True
                        except TimeoutException:
                            continue
                    
                    print("⚠️ Click succeeded but unclear if navigation occurred")
                    return True
                    
            except Exception as nav_error:
                print(f"❌ Navigation check failed: {nav_error}")
                return False
        else:
            print(f"❌ Client '{last_name} {first_name}' not found in search results")
            
            # Debug: Show available clients
            try:
                all_client_links = driver.find_elements(By.XPATH, "//div[@id='ctl00_MainContent_pnlClientList']//a[@title]")
                if all_client_links:
                    print(f"📋 Available clients in search results:")
                    for i, link in enumerate(all_client_links[:10]):
                        title = link.get_attribute("title") or link.text or "No title"
                        client_id = link.get_attribute("clientid") or "No ID"
                        print(f"   {i+1}. {title} (ID: {client_id})")
                else:
                    print("📋 No client links found in results panel")
            except Exception as debug_error:
                print(f"⚠️ Could not retrieve client list for debugging: {debug_error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error in find_and_click_client: {str(e)}")
        return False


def search_and_open_client(driver, last_name, first_name, original_last_name=None):
    """Complete workflow to search for and open a client's details page."""
    try:
        # Use original_last_name for search if provided, otherwise use last_name
        search_last_name = original_last_name if original_last_name else last_name
        
        print(f"\n--- Starting client search workflow ---")
        print(f"Display Name: {last_name}, {first_name}")
        if original_last_name and original_last_name != last_name:
            print(f"Search Name: {search_last_name}, {first_name}")
        
        # Step 1: Navigate to clients (opens new tab)
        print("Step 1: Navigating to Clients menu...")
        navigation_success = navigate_to_clients(driver)
        if not navigation_success:
            print("❌ Failed to navigate to Clients menu")
            return False
        print(f"Current tab count after navigation: {len(driver.window_handles)}")
        
        # Step 2: Search for the client
        print("Step 2: Performing client search...")
        search_term = search_client(driver, search_last_name, first_name)
        print(f"Searched for: {search_term}")
        
        # Step 3: Find and click on the client
        print("Step 3: Looking for client in results...")
        
        # Store current handles before clicking client
        current_handles = set(driver.window_handles)
        current_tab = driver.current_window_handle
        
        success = find_and_click_client(driver, last_name, first_name)
        
        # Step 4: Close the client search tab after processing
        if success:
            print(f"✅ Successfully opened client details for: {last_name}, {first_name}")
            print(f"Tab count after client click: {len(driver.window_handles)}")
            
            # Close the client search tab and keep the client details tab
            try:
                if len(driver.window_handles) > len(current_handles):
                    print("🗂️ Closing client search tab...")
                    driver.switch_to.window(current_tab)
                    driver.close()
                    
                    # Switch to the remaining tab (client details or original)
                    remaining_handles = driver.window_handles
                    if remaining_handles:
                        driver.switch_to.window(remaining_handles[-1])
                        print(f"✅ Closed search tab, switched to client details tab")
                    
                print(f"Final tab count after cleanup: {len(driver.window_handles)}")
            except Exception as e:
                print(f"⚠️ Error closing search tab: {e}")
            
            return True
        else:
            print(f"❌ Failed to find client in results: {last_name}, {first_name}")
            
            # Close the search tab even if client not found
            try:
                print("🗂️ Closing search tab (client not found)...")
                driver.close()
                
                # Switch back to original tab if available
                remaining_handles = driver.window_handles
                if remaining_handles:
                    driver.switch_to.window(remaining_handles[0])
                    print("✅ Closed search tab, returned to original tab")
            except Exception as e:
                print(f"⚠️ Error closing search tab after failure: {e}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error during client search workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def click_personal_data_tab(driver):
    """Click on Personal Data tab after opening client details."""
    print("🎯 Looking for Personal Data tab...")
    
    try:
        # Look for Personal Data tab
        personal_data_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, PERSONAL_DATA_TAB_ID))
        )
        
        print("✅ Found Personal Data tab")
        driver.execute_script("arguments[0].click();", personal_data_tab)
        print("✅ Clicked Personal Data tab")
        
        # Wait for Personal Data content to load
        wait_document_ready(driver)
        time.sleep(2)
        
        return True
        
    except TimeoutException:
        print("❌ Personal Data tab not found")
        return False
    except Exception as e:
        print(f"❌ Error clicking Personal Data tab: {e}")
        return False


def extract_personal_data(driver, client_name):
    """Extract personal data fields from the client details page."""
    print(f"📊 Extracting personal data for: {client_name}")
    
    extracted_data = {
        'client_name': client_name,
        'phone_1': '',
        'phone_2': '',
        'service_start': '',
        'service_end': '',
        'inquiry_date': '',
        'assessment': '',
        'case_manager': '',
        'med_record': '',
        'referral_number': '',
        'address_1': '',
        'address_2': '',
        'city': '',
        'state': '',
        'zip': '',
        'county': ''
    }
    
    try:
        # Extract each field using the field mappings from config
        for field_name, field_id in PERSONAL_DATA_FIELDS.items():
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                
                # Check if it's a dropdown (select) element
                if element.tag_name.lower() == 'select':
                    from selenium.webdriver.support.ui import Select
                    select = Select(element)
                    # Get selected option text, skip if it's a placeholder like "-----Select-----"
                    selected_text = select.first_selected_option.text if select.first_selected_option else ''
                    value = selected_text if selected_text and not selected_text.startswith('-----') else ''
                else:
                    value = element.get_attribute('value') or ''
                
                extracted_data[field_name] = value.strip()
                print(f"  ✅ {field_name}: '{value.strip()}'")
                
            except TimeoutException:
                print(f"  ⚠️ {field_name}: Not found")
            except Exception as e:
                print(f"  ❌ {field_name}: Error - {e}")
        
        print(f"📋 Extraction completed for {client_name}")
        return extracted_data
        
    except Exception as e:
        print(f"❌ Error during data extraction: {e}")
        return extracted_data


def process_client_with_personal_data(driver, client_name, last_name, first_name, original_last_name=None):
    """Process a single client: search, open, click Personal Data, extract info, then close tab."""
    print(f"\n🔍 Processing client with Personal Data: {client_name}")
    
    # Store the original window handle before opening new tabs
    try:
        original_window = driver.current_window_handle
        original_handles_count = len(driver.window_handles)
        print(f"📋 Starting with {original_handles_count} tab(s)")
    except Exception as e:
        print(f"⚠️ Could not get original window handle: {e}")
        original_window = None
    
    try:
        # Step 1: Search and open client details (opens new tab)
        success = search_and_open_client(driver, last_name, first_name, original_last_name)
        if not success:
            return None
        
        # Step 2: Click Personal Data tab
        if not click_personal_data_tab(driver):
            # Close the client details tab before returning
            _close_client_tab(driver, original_window)
            return None
        
        # Step 3: Extract personal data
        extracted_data = extract_personal_data(driver, client_name)
        
        # Step 4: Close the client details tab after extraction
        _close_client_tab(driver, original_window)
        
        return extracted_data
        
    except Exception as e:
        print(f"❌ Error processing client {client_name}: {e}")
        # Attempt to close tab even on error
        try:
            _close_client_tab(driver, original_window)
        except:
            pass
        return None


def _close_client_tab(driver, original_window=None):
    """Close the current client details tab and return to the original window."""
    try:
        current_handles = driver.window_handles
        print(f"🗂️ Closing client tab (currently {len(current_handles)} tab(s) open)...")
        
        # Close the current tab (which should be the client details tab)
        driver.close()
        print("✅ Client details tab closed")
        
        # Switch back to the original window or the first available window
        remaining_handles = driver.window_handles
        if remaining_handles:
            if original_window and original_window in remaining_handles:
                driver.switch_to.window(original_window)
                print(f"↩️ Switched back to original window")
            else:
                driver.switch_to.window(remaining_handles[0])
                print(f"↩️ Switched to first available window")
            
            print(f"📋 Now {len(remaining_handles)} tab(s) remaining")
        else:
            print("⚠️ No windows remaining after closing tab")
            
    except Exception as e:
        print(f"⚠️ Error closing client tab: {e}")
        # Try to switch to any available window
        try:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
                print("↩️ Switched to first available window (fallback)")
        except:
            pass


def _close_existing_client_tabs(driver):
    """Close any existing Client List tabs to prevent 'already opened' conflicts."""
    try:
        current_handle = driver.current_window_handle
        all_handles = driver.window_handles
        
        print(f"🔍 Checking {len(all_handles)} tabs for existing Client List pages...")
        
        closed_count = 0
        for handle in all_handles:
            if handle == current_handle:
                continue  # Don't close the current tab
            
            try:
                driver.switch_to.window(handle)
                current_url = driver.current_url
                page_title = driver.title
                
                # Check if this is a Client List page
                if ("client" in current_url.lower() or 
                    "client" in page_title.lower() or
                    "ClientList" in current_url):
                    
                    print(f"🗂️ Closing existing Client List tab: {page_title[:50]}...")
                    driver.close()
                    closed_count += 1
                    
            except Exception as e:
                print(f"⚠️ Error checking tab {handle}: {e}")
                continue
        
        # Switch back to original tab
        try:
            driver.switch_to.window(current_handle)
            print(f"✅ Closed {closed_count} existing Client List tab(s)")
        except Exception as e:
            # Original tab might have been closed, switch to first available
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
                print(f"✅ Closed {closed_count} tab(s), switched to available tab")
            
    except Exception as e:
        print(f"❌ Error closing existing Client List tabs: {e}")
        # Ensure we're in a valid window
        try:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
