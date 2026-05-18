import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, NoSuchWindowException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from core.storage_manager import StorageManager


class BrowserManager:
    def __init__(self, root_path: Path, storage: StorageManager, logger) -> None:
        self.root_path = root_path
        self.storage = storage
        self.logger = logger
        self.driver: Optional[webdriver.Chrome] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._handles: Set[str] = set()
        self._injector = None
        self._listeners: List[Callable[[], None]] = []

    def set_injector(self, injector) -> None:
        self._injector = injector

    def start(self) -> bool:
        if self.driver is not None:
            return True
        try:
            self.logger.info("Starting browser session")
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            browser_config = self.storage.config.get("browser", {})
            if browser_config.get("headless", False):
                options.add_argument("--headless=new")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.set_window_size(1440, 900)
            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            self.driver.execute_cdp_cmd("Page.enable", {})
            self._handles = set(self.driver.window_handles)
            self._start_monitor()
            return True
        except Exception as error:
            self.logger.exception("Browser start failed: %s", error)
            self.shutdown()
            return False

    def get_performance_logs(self) -> List[Dict[str, Any]]:
        if self.driver is None:
            return []
        try:
            return self.driver.get_log("performance")
        except WebDriverException as error:
            self.logger.debug("Failed to read performance logs: %s", error)
            return []

    def get_response_body(self, request_id: str) -> str:
        if self.driver is None:
            return ""
        try:
            response = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            body = response.get("body", "")
            if response.get("base64Encoded"):
                body = json.loads(body)
            return body
        except Exception as error:
            self.logger.debug("Failed to get response body: %s", error)
            return ""

    def extract_visible_job_name(self, job_id: Optional[int] = None) -> str:
        if self.driver is None:
            return ""
        target_expression = f".wjob-{job_id}" if job_id else ".jobwindow"
        script = f"""
            var container = document.querySelector('{target_expression}') || document.querySelector('.jobwindow') || document.querySelector('.window_content');
            if (!container) return '';
            var title = container.querySelector('.headline, .window_header h1, .window_header h2, .job_title, .jobhead');
            if (title) return title.textContent.trim();
            return container.textContent.trim().split('\n')[0] || '';
        """
        result = self.execute_script(script, "")
        return str(result or "").strip()

    def extract_visible_town_name(self, unit_id: Optional[int] = None) -> str:
        if self.driver is None:
            return ""
        script = """
            var container = document.querySelector('.townwindow') || document.querySelector('.townView') || document.querySelector('.window_content');
            if (!container) return '';
            var title = container.querySelector('.town_name, .headline, .window_header h1, .window_header h2');
            if (title) return title.textContent.trim();
            return container.textContent.trim().split('\n')[0] || '';
        """
        result = self.execute_script(script, "")
        return str(result or "").strip()

    def extract_current_task_window(self) -> Optional[Dict[str, Any]]:
        if self.driver is None:
            return None
        script = """
            function queryField(name) {
                var input = document.querySelector("input[name='" + name + "']") || document.querySelector("input[name='tasks[0][" + name + "]']");
                return input ? input.value || input.textContent || '' : '';
            }
            var jobId = queryField('jobId') || queryField('job_id');
            var unitId = queryField('unitId');
            var x = queryField('x');
            var y = queryField('y');
            var duration = queryField('duration');
            var typeValue = queryField('type') || queryField('taskType');
            var title = '';
            var headline = document.querySelector('.headline, .window_header h1, .window_header h2, .job_title, .town_name');
            if (headline) title = headline.textContent.trim();
            return {
                jobId: jobId ? parseInt(jobId, 10) : null,
                unitId: unitId ? parseInt(unitId, 10) : null,
                x: x ? parseInt(x, 10) : null,
                y: y ? parseInt(y, 10) : null,
                duration: duration ? parseInt(duration, 10) : null,
                type: typeValue || '',
                name: title || '',
            };
        """
        result = self.execute_script(script, None)
        if not isinstance(result, dict):
            return None
        return result

    def _start_monitor(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self) -> None:
        while not self._stop_event.wait(1.5):
            if self.driver is None:
                continue
            self._detect_window_changes()
            self._trigger_reinjection()

    def _detect_window_changes(self) -> None:
        try:
            handles = set(self.driver.window_handles)
            if handles != self._handles:
                new_handles = handles - self._handles
                self._handles = handles
                if new_handles:
                    self.logger.debug("Detected new browser windows: %s", new_handles)
                    self._notify_listeners()
        except WebDriverException as error:
            self.logger.warning("Failed to inspect browser windows: %s", error)
            self._recover_browser()

    def _trigger_reinjection(self) -> None:
        if self._injector is None or self.driver is None:
            return
        if self.driver.current_window_handle not in self._handles:
            return
        try:
            self._injector.inject(self.driver)
        except Exception as error:
            self.logger.debug("Injector reinjection failed: %s", error)

    def _recover_browser(self) -> None:
        if not self.storage.config.get("browser", {}).get("auto_reconnect", True):
            return
        self.logger.warning("Attempting browser recovery")
        self.shutdown()
        time.sleep(2)
        self.start()

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception as error:
                self.logger.exception("Browser listener callback failed: %s", error)

    def register_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def navigate_to(self, url: str) -> bool:
        if self.driver is None:
            return False
        try:
            self.logger.debug("Navigating to %s", url)
            self.driver.get(url)
            return True
        except WebDriverException as error:
            self.logger.exception("Navigation failed: %s", error)
            return False

    def login(self, username: str, password: str, world_text: str = "Alamogordo") -> bool:
        if self.driver is None:
            return False
        try:
            wait = WebDriverWait(self.driver, 25)
            self.driver.get(self.storage.config.get("browser", {}).get("base_url", ""))
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
            self.driver.find_element(By.NAME, "userpassword").send_keys(password)
            self.driver.find_element(By.ID, "loginButton").click()
            world_xpath = f"//a[contains(text(), '{world_text}')]"
            wait.until(EC.element_to_be_clickable((By.XPATH, world_xpath))).click()
            self.logger.info("Login completed for user %s", username)
            return True
        except Exception as error:
            self.logger.exception("Login failed: %s", error)
            return False

    def execute_script(self, script: str, fallback: Any = None) -> Any:
        if self.driver is None:
            return fallback
        try:
            return self.driver.execute_script(script)
        except (JavascriptException, WebDriverException, NoSuchWindowException) as error:
            self.logger.warning("Script execution failed: %s", error)
            return fallback

    def inject_js(self, script_text: str) -> bool:
        if self.driver is None:
            return False
        try:
            self.driver.execute_script(script_text)
            self.logger.debug("Injected JS script successfully")
            return True
        except Exception as error:
            self.logger.warning("JS injection failed: %s", error)
            return False

    def fetch_local_storage(self, key: str) -> Optional[str]:
        return self.execute_script(f"return window.localStorage.getItem('{key}');", None)

    def clear_local_storage(self, key: str) -> None:
        self.execute_script(f"window.localStorage.removeItem('{key}');")

    def shutdown(self) -> None:
        self._stop_event.set()
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self.logger.info("Browser session terminated")
