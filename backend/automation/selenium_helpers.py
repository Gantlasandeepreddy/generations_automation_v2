"""
Selenium utility functions for web automation.
Handles browser management, element finding, and error recovery.
"""

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from automation.config import MAX_STEP_DELAY, DEFAULT_TIMEOUT, FRAME_TIMEOUT


def build_driver(download_dir: Path, session_id: str, headless: bool = True) -> webdriver.Chrome:
    """Build Chrome WebDriver with optimized settings for automation."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--incognito")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")

    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_dir)})
    except Exception:
        pass
    return driver


def wait_document_ready(driver, timeout=30):
    """Wait for the document to be fully loaded with alert handling."""
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
    except Exception as e:
        # Check if there's an alert interfering
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"⚠️ Alert detected during document ready wait: {alert_text}")
            alert.accept()
            print("✅ Alert dismissed, retrying document ready check...")
            # Retry once after handling alert
            WebDriverWait(driver, timeout//2).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception:
            # Re-raise original exception if not an alert issue
            raise e


def slow_step_pause(delay: float):
    """Pause execution with a maximum cap."""
    time.sleep(min(delay, MAX_STEP_DELAY))


def set_input_value_by_id_js(driver, element_id: str, value: str) -> bool:
    """Set input field value using JavaScript for reliability."""
    return driver.execute_script(
        """
        var el = document.getElementById(arguments[0]);
        if (!el) return false;
        el.value = '';
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.value = arguments[1];
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
        """,
        element_id, value
    )


def find_element_in_any_frame(driver, locator, condition="clickable", total_timeout=DEFAULT_TIMEOUT):
    """
    Find element in main content or any iframe with enhanced error handling.
    
    Args:
        driver: WebDriver instance
        locator: Tuple of (By.TYPE, selector)
        condition: "clickable", "visible", or "present"
        total_timeout: Maximum time to search
        
    Returns:
        Tuple of (frame_name, element)
    """
    end_time = time.time() + total_timeout
    last_exc = None
    
    while time.time() < end_time:
        # Try main content first
        driver.switch_to.default_content()
        try:
            if condition == "clickable":
                el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(locator))
            elif condition == "visible":
                el = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(locator))
            else:
                el = WebDriverWait(driver, 2).until(EC.presence_of_element_located(locator))
            return ("main", el)
        except Exception as e:
            last_exc = e
            
        # Try all iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, iframe in enumerate(iframes, start=1):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(iframe)
            except Exception as e:
                last_exc = e
                continue
            try:
                if condition == "clickable":
                    el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(locator))
                elif condition == "visible":
                    el = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(locator))
                else:
                    el = WebDriverWait(driver, 2).until(EC.presence_of_element_located(locator))
                return (f"iframe#{idx}", el)
            except Exception as e:
                last_exc = e
                continue
        time.sleep(0.5)
    
    driver.switch_to.default_content()
    raise TimeoutException(f"Element {locator} not found/clickable in any frame: {last_exc}")


def wait_invisibility_in_any_frame(driver, locator, total_timeout=DEFAULT_TIMEOUT):
    """Wait for element to become invisible in all frames."""
    end_time = time.time() + total_timeout
    
    while time.time() < end_time:
        invisible_everywhere = True
        driver.switch_to.default_content()
        
        try:
            if not WebDriverWait(driver, 1).until(EC.invisibility_of_element_located(locator)):
                invisible_everywhere = False
        except Exception:
            pass
            
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(iframe)
            except Exception:
                continue
            try:
                if not WebDriverWait(driver, 1).until(EC.invisibility_of_element_located(locator)):
                    invisible_everywhere = False
            except Exception:
                pass
                
        if invisible_everywhere:
            driver.switch_to.default_content()
            return True
        time.sleep(0.2)
        
    driver.switch_to.default_content()
    return False


def try_switch_to_panel_context(driver, panel_id: str) -> None:
    """Switch to the correct frame context for a panel."""
    driver.switch_to.default_content()
    try:
        WebDriverWait(driver, FRAME_TIMEOUT).until(EC.visibility_of_element_located((By.ID, panel_id)))
        return
    except TimeoutException:
        pass
        
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        driver.switch_to.default_content()
        driver.switch_to.frame(iframe)
        try:
            WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.ID, panel_id)))
            return
        except TimeoutException:
            continue
    driver.switch_to.default_content()
    raise TimeoutException(f"Panel {panel_id} not visible")


def handle_warning_popups(driver):
    """Handle any warning popups that might appear."""
    try:
        alert = driver.switch_to.alert
        alert.accept()
        return True
    except Exception:
        pass
    
    warning_selectors = [
        "//input[@type='button' and (@value='OK' or @value='Ok')]",
        "//button[contains(text(), 'OK') or contains(text(), 'Ok')]",
        "//div[contains(text(), 'Please select') or contains(text(), 'Display Report')]/..//button",
    ]
    
    for selector in warning_selectors:
        try:
            driver.switch_to.default_content()
            ok_button = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, selector)))
            if ok_button.is_displayed():
                driver.execute_script("arguments[0].click();", ok_button)
                time.sleep(0.5)
                return True
        except TimeoutException:
            pass
    
    # Try in iframes
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            for selector in warning_selectors:
                try:
                    ok_button = WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if ok_button.is_displayed():
                        driver.execute_script("arguments[0].click();", ok_button)
                        driver.switch_to.default_content()
                        time.sleep(0.5)
                        return True
                except TimeoutException:
                    continue
    except Exception:
        pass
    
    driver.switch_to.default_content()
    return False


def retry_on_stale_element(func, max_retries=3, delay=2):
    """
    Wrapper function to retry operations that might encounter stale element references.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        delay: Base delay between retries (progressive)
        
    Returns:
        Result of the function execution
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = func()
            if attempt > 0:
                print(f"✅ Operation succeeded after {attempt + 1} attempts")
            return result
            
        except StaleElementReferenceException as e:
            last_exception = e
            print(f"🔄 Stale element detected on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}")
            
            if attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("❌ Max retries reached for stale element handling")
                raise e
                
        except (TimeoutException, NoSuchElementException) as e:
            last_exception = e
            print(f"⚠️ Element not found on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}")
            
            if attempt < max_retries - 1:
                wait_time = delay
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("❌ Max retries reached for element finding")
                raise e
                
        except Exception as e:
            print(f"❌ Non-retryable error: {type(e).__name__}: {str(e)[:100]}")
            raise e
    
    if last_exception:
        raise last_exception


def safe_find_and_click(driver, locator, timeout=DEFAULT_TIMEOUT, method="javascript"):
    """Safely find and click an element with stale element retry logic."""
    def _click_operation():
        if isinstance(locator, tuple):
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        else:
            element = locator
            
        if method == "javascript":
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", element)
        else:
            element.click()
        
        return True
    
    return retry_on_stale_element(_click_operation)


def safe_select_dropdown(driver, dropdown_id, value, timeout=DEFAULT_TIMEOUT):
    """Safely select from dropdown with stale element retry logic."""
    def _select_operation():
        time.sleep(0.5)
        dropdown_element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, dropdown_id)))
        dropdown = Select(dropdown_element)
        dropdown.select_by_value(value)
        return True
    
    return retry_on_stale_element(_select_operation)


def refresh_page_context(driver):
    """Refresh the page context to avoid stale elements."""
    try:
        driver.switch_to.default_content()
        wait_document_ready(driver)
        time.sleep(1)
        driver.execute_script("return document.readyState;")
        print("Page context refreshed")
    except Exception as e:
        print(f"Warning: Could not refresh page context: {e}")
        try:
            print("Attempting page refresh due to context issues...")
            driver.refresh()
            wait_document_ready(driver)
            time.sleep(2)
            print("Page refresh completed")
        except Exception as e2:
            print(f"Warning: Page refresh also failed: {e2}")


def wait_for_downloads(download_dir: Path, timeout: int = 180) -> bool:
    """Wait for downloads to complete (no .crdownload files)."""
    start = time.time()
    while time.time() - start < timeout:
        if not any(download_dir.glob("*.crdownload")):
            return True
        time.sleep(0.5)
    return False
