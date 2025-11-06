import time
from selenium.common.exceptions import WebDriverException


class GenerationsSession:
    """
    Manages Generations IDB session with idle timeout prevention.
    Keeps session alive by performing lightweight operations before idle threshold.
    """

    def __init__(self, driver, credentials, run_id):
        self.driver = driver
        self.credentials = credentials
        self.run_id = run_id
        self.last_activity = time.time()
        self.idle_threshold = 300  # 5 minutes in seconds
        self.relogin_attempts = 0
        self.max_relogin_attempts = 3

    def keep_alive(self):
        """
        Check idle time and ping session if approaching timeout.
        Prevents Generations from logging out due to inactivity.
        """
        idle_time = time.time() - self.last_activity

        if idle_time > self.idle_threshold:
            try:
                self.driver.execute_script("return document.readyState")
                self.last_activity = time.time()
                print(f"[{self.run_id}] Keep-alive ping sent (idle for {int(idle_time)}s)")
            except WebDriverException as e:
                print(f"[{self.run_id}] Session appears dead: {e}")
                self.relogin()

    def relogin(self):
        """
        Re-authenticate to Generations if session expired.
        Raises exception if max attempts exceeded.
        """
        if self.relogin_attempts >= self.max_relogin_attempts:
            raise Exception(f"Max re-login attempts ({self.max_relogin_attempts}) exceeded")

        self.relogin_attempts += 1
        print(f"[{self.run_id}] Attempting re-login ({self.relogin_attempts}/{self.max_relogin_attempts})")

        try:
            from automation.report_automation import login_and_open_report_writer

            self.driver = login_and_open_report_writer(
                self.driver,
                self.credentials['agency_id'],
                self.credentials['email'],
                self.credentials['password']
            )
            self.last_activity = time.time()
            self.relogin_attempts = 0
            print(f"[{self.run_id}] Re-login successful")
        except Exception as e:
            raise Exception(f"Re-login failed: {e}")

    def update_activity(self):
        """Call this after every successful Selenium operation"""
        self.last_activity = time.time()
