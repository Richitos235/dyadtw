import json
import threading
import time
from typing import Any, Dict, Optional

from core.browser_manager import BrowserManager
from database.database_manager import DatabaseManager
from core.parser_engine import ParserEngine
from models.job_model import JobRecord
from models.town_model import TownRecord


class NetworkSniffer:
    def __init__(
        self,
        browser_manager: BrowserManager,
        parser_engine: ParserEngine,
        database_manager: DatabaseManager,
        logger,
    ) -> None:
        self.browser_manager = browser_manager
        self.parser_engine = parser_engine
        self.database_manager = database_manager
        self.logger = logger
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop_event = threading.Event()
        self._pending_town_requests: Dict[str, TownRecord] = {}

    def start(self) -> None:
        if self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread.start()
        self.logger.info("Network sniffer started")

    def stop(self) -> None:
        self._stop_event.set()
        self.logger.info("Network sniffer stopping")

    def _run(self) -> None:
        while not self._stop_event.wait(0.25):
            self._poll_logs()

    def _poll_logs(self) -> None:
        entries = self.browser_manager.get_performance_logs()
        for entry in entries:
            try:
                payload = json.loads(entry.get("message", "{}"))["message"]
            except Exception:
                continue
            method = payload.get("method")
            params = payload.get("params", {})
            if method == "Network.requestWillBeSent":
                self._handle_request(params)
            elif method == "Network.responseReceived":
                self._handle_response(params)

    def _handle_request(self, params: Dict[str, Any]) -> None:
        request = params.get("request", {})
        url = request.get("url", "")
        post_data = request.get("postData") or request.get("payload") or ""
        parsed = self.parser_engine.parse_task_request(url, post_data)
        if not parsed:
            return
        if parsed["type"] == "job":
            job_name = self.browser_manager.extract_visible_job_name(parsed.get("job_id"))
            record = JobRecord(
                job_id=parsed["job_id"],
                name=job_name or f"Job {parsed['job_id']}",
                x=parsed["x"],
                y=parsed["y"],
                duration=parsed["duration"],
            )
            self.database_manager.upsert_job(record)
            self.logger.info("Captured learned job %s", record.name)
        elif parsed["type"] == "town":
            town_name = self.browser_manager.extract_visible_town_name(parsed.get("unit_id"))
            record = TownRecord(
                unit_id=parsed["unit_id"],
                town_name=town_name or f"Town {parsed['unit_id']}",
                x=parsed["x"],
                y=parsed["y"],
                walk_time_seconds=None,
            )
            self._pending_town_requests[params.get("requestId")] = record
            self.database_manager.upsert_town(record)
            self.logger.info("Captured learned town move %s", record.town_name)

    def _handle_response(self, params: Dict[str, Any]) -> None:
        request_id = params.get("requestId")
        if request_id not in self._pending_town_requests:
            return
        try:
            body_response = self.browser_manager.get_response_body(request_id)
        except Exception as error:
            self.logger.debug("Unable to read response body for %s: %s", request_id, error)
            return
        parsed = self.parser_engine.parse_task_response(body_response)
        if not parsed:
            return
        record = self._pending_town_requests.pop(request_id, None)
        if not record:
            return
        record.walk_time_seconds = parsed.get("walk_time_seconds")
        self.database_manager.upsert_town(record)
        self.logger.info("Updated town %s with walk_time %s", record.town_name, record.walk_time_seconds)
