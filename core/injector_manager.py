from pathlib import Path
from typing import Any, Dict, List, Optional

from core.browser_manager import BrowserManager


class InjectorManager:
    STORAGE_KEY = "westbot_job_add"

    def __init__(self, script_path: Path, browser: BrowserManager, logger) -> None:
        self.script_path = script_path
        self.browser = browser
        self.logger = logger
        self.script_text = self.script_path.read_text(encoding="utf-8")

    def inject(self, driver: Any) -> None:
        try:
            driver.execute_script(self.script_text)
        except Exception as error:
            self.logger.debug("Inject script error: %s", error)

    def fetch_job_events(self) -> List[Dict[str, Any]]:
        raw_value = self.browser.fetch_local_storage(self.STORAGE_KEY)
        if raw_value is None:
            return []
        try:
            import json

            payload = json.loads(raw_value)
            if isinstance(payload, dict):
                return [payload]
            if isinstance(payload, list):
                return payload
        except Exception as error:
            self.logger.warning("Failed to parse injected payload: %s", error)
        return []

    def consume_job_events(self) -> List[Dict[str, Any]]:
        jobs = self.fetch_job_events()
        if jobs:
            self.browser.clear_local_storage(self.STORAGE_KEY)
        return jobs
