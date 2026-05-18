import json
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from models.job_models import JobDefinition
from models.task_models import TaskModel


class StorageManager:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.config_path = root_path / "config.json"
        self.jobs_path = root_path / "jobs_database.json"
        self.lock = RLock()
        self.config = self._load_config()

    def _atomic_write(self, path: Path, payload: str) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as temp_file:
            temp_file.write(payload)
        temp_path.replace(path)

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except json.JSONDecodeError:
            return default

    def _load_config(self) -> Dict[str, Any]:
        with self.lock:
            data = self._load_json(self.config_path, {})
            return {
                "browser": data.get("browser", {}),
                "scheduler": data.get("scheduler", {}),
                "logging": data.get("logging", {}),
                "ui": data.get("ui", {}),
                "queue": data.get("queue", []),
                "credentials": data.get("credentials", {}),
                "database": data.get("database", {}),
            }

    def save_config(self) -> None:
        with self.lock:
            self._atomic_write(self.config_path, json.dumps(self.config, indent=2, ensure_ascii=False))

    def get_credentials(self) -> Dict[str, str]:
        return self.config.get("credentials", {"username": "", "password": ""})

    def save_credentials(self, username: str, password: str) -> None:
        with self.lock:
            self.config["credentials"] = {"username": username, "password": password}
            self.save_config()

    def get_database_path(self) -> Path:
        db_relative = self.config.get("database", {}).get("path", "westbot_v6.db")
        return self.root_path / db_relative

    def load_jobs(self) -> List[JobDefinition]:
        raw_entries = self._load_json(self.jobs_path, [])
        jobs: List[JobDefinition] = []
        for item in raw_entries:
            try:
                jobs.append(JobDefinition.from_dict(item))
            except ValueError:
                continue
        return jobs

    def save_jobs(self, jobs: List[JobDefinition]) -> None:
        with self.lock:
            payload = [job.to_dict() for job in jobs]
            self._atomic_write(self.jobs_path, json.dumps(payload, indent=2, ensure_ascii=False))

    def load_queue(self) -> List[TaskModel]:
        with self.lock:
            entries = self.config.get("queue", [])
            tasks: List[TaskModel] = []
            for item in entries:
                try:
                    tasks.append(TaskModel.from_dict(item))
                except ValueError:
                    continue
            return tasks

    def save_queue(self, tasks: List[TaskModel]) -> None:
        with self.lock:
            self.config["queue"] = [task.to_dict() for task in tasks]
            self.save_config()

    def create_default_config(self) -> None:
        with self.lock:
            if not self.config_path.exists():
                self.config = {
                    "browser": {
                        "headless": False,
                        "delay_multiplier": 1.0,
                        "auto_reconnect": True,
                        "base_url": "https://zz1.beta.the-west.net/",
                    },
                    "scheduler": {
                        "poll_interval_seconds": 1,
                        "max_queue_length": 12,
                        "job_retry_limit": 2,
                        "job_cooldown_seconds": 4,
                    },
                    "logging": {
                        "level": "DEBUG",
                        "file": "westbot_v6.log",
                    },
                    "ui": {
                        "theme": "dark",
                    },
                    "credentials": {
                        "username": "",
                        "password": "",
                    },
                    "database": {
                        "path": "westbot_v6.db",
                    },
                    "queue": [],
                }
                self.save_config()
            else:
                self.config = self._load_config()
