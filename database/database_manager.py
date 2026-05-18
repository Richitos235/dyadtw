import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Callable, List, Optional

from models.job_model import JobRecord
from models.town_model import TownRecord


class DatabaseManager:
    def __init__(self, db_path: Path, logger) -> None:
        self.db_path = db_path
        self.logger = logger
        self._lock = RLock()
        self._listeners: List[Callable[[], None]] = []
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(job_id, x, y)
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS towns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id INTEGER NOT NULL,
                    town_name TEXT NOT NULL,
                    x INTEGER,
                    y INTEGER,
                    walk_time_seconds INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(unit_id, x, y)
                );
                """
            )
            self.connection.commit()
            self.logger.info("Database schema initialized: %s", self.db_path)

    def register_listener(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        for callback in list(self._listeners):
            try:
                callback()
            except Exception as error:
                self.logger.exception("Database listener failed: %s", error)

    def upsert_job(self, record: JobRecord) -> int:
        now = datetime.utcnow().isoformat()
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id, duration, name FROM jobs WHERE job_id = ? AND x = ? AND y = ?;",
                (record.job_id, record.x, record.y),
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE jobs SET name = ?, duration = ?, updated_at = ? WHERE id = ?;",
                    (record.name, record.duration, now, row["id"]),
                )
                record_id = row["id"]
                self.logger.debug("Updated existing job record %s", record_id)
            else:
                cursor.execute(
                    "INSERT INTO jobs (job_id, name, x, y, duration, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                    (record.job_id, record.name, record.x, record.y, record.duration, now, now),
                )
                record_id = cursor.lastrowid
                self.logger.debug("Inserted learned job record %s", record_id)
            self.connection.commit()
            self._notify_listeners()
            return record_id

    def upsert_town(self, record: TownRecord) -> int:
        now = datetime.utcnow().isoformat()
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id FROM towns WHERE unit_id = ? AND x = ? AND y = ?;",
                (record.unit_id, record.x, record.y),
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE towns SET town_name = ?, walk_time_seconds = ?, updated_at = ? WHERE id = ?;",
                    (record.town_name, record.walk_time_seconds, now, row["id"]),
                )
                record_id = row["id"]
                self.logger.debug("Updated existing town record %s", record_id)
            else:
                cursor.execute(
                    "INSERT INTO towns (unit_id, town_name, x, y, walk_time_seconds, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    (record.unit_id, record.town_name, record.x, record.y, record.walk_time_seconds, now, now),
                )
                record_id = cursor.lastrowid
                self.logger.debug("Inserted learned town record %s", record_id)
            self.connection.commit()
            self._notify_listeners()
            return record_id

    def list_jobs(self) -> List[JobRecord]:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY updated_at DESC;")
            rows = cursor.fetchall()
            return [JobRecord.from_row(row) for row in rows]

    def list_towns(self) -> List[TownRecord]:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM towns ORDER BY updated_at DESC;")
            rows = cursor.fetchall()
            return [TownRecord.from_row(row) for row in rows]

    def list_all(self) -> List[object]:
        return self.list_jobs() + self.list_towns()

    def close(self) -> None:
        with self._lock:
            self.connection.close()
