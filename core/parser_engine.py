import json
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, unquote_plus


class ParserEngine:
    def __init__(self, logger) -> None:
        self.logger = logger

    @staticmethod
    def _parse_body(body: str) -> Dict[str, Any]:
        decoded = unquote_plus(body)
        parsed = parse_qs(decoded, keep_blank_values=True)
        return {key: values[0] for key, values in parsed.items()}

    def parse_task_request(self, url: str, body: str) -> Optional[Dict[str, Any]]:
        if not url or "window=task" not in url or "action=add" not in url:
            return None
        try:
            parsed = self._parse_body(body)
        except Exception as error:
            self.logger.debug("Failed to parse request body: %s", error)
            return None

        task_type = parsed.get("tasks[0][taskType]") or parsed.get("tasks[0][type]")
        if task_type == "job":
            try:
                return {
                    "type": "job",
                    "job_id": int(parsed.get("tasks[0][jobId]", 0)),
                    "x": int(parsed.get("tasks[0][x]", 0)),
                    "y": int(parsed.get("tasks[0][y]", 0)),
                    "duration": int(parsed.get("tasks[0][duration]", 0)),
                }
            except ValueError:
                return None
        if task_type in {"town", "walk"}:
            try:
                return {
                    "type": "town",
                    "unit_id": int(parsed.get("tasks[0][unitId]", 0)),
                    "x": int(parsed.get("tasks[0][x]", 0)),
                    "y": int(parsed.get("tasks[0][y]", 0)),
                    "task_type": task_type,
                }
            except ValueError:
                return None
        return None

    def parse_task_response(self, response_body: str) -> Optional[Dict[str, Any]]:
        if not response_body:
            return None
        try:
            payload = json.loads(response_body)
        except Exception:
            return None
        if isinstance(payload, dict) and "date_start" in payload and "date_done" in payload:
            try:
                walk_time = int(float(payload["date_done"]) - float(payload["date_start"]))
                return {"walk_time_seconds": walk_time}
            except (TypeError, ValueError):
                return None
        return None
