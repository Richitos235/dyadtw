from typing import Any, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.browser_manager import BrowserManager
from database.database_manager import DatabaseManager
from core.queue_manager import QueueManager
from models.job_model import JobRecord
from models.task_models import TaskModel, TaskType
from models.town_model import TownRecord


class JobsDatabaseTab(QWidget):
    def __init__(
        self,
        queue_manager: QueueManager,
        database_manager: DatabaseManager,
        browser_manager: BrowserManager,
        logger,
    ) -> None:
        super().__init__()
        self.queue_manager = queue_manager
        self.database_manager = database_manager
        self.browser_manager = browser_manager
        self.logger = logger
        self._build_ui()
        self.database_manager.register_listener(self.refresh)
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        control_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search captured jobs and towns")
        self.search_input.textChanged.connect(self.refresh)

        self.type_selector = QComboBox()
        self.type_selector.addItems(["All", "Jobs", "Towns"])
        self.type_selector.currentTextChanged.connect(self.refresh)

        self.repeat_selector = QSpinBox()
        self.repeat_selector.setRange(1, 20)
        self.repeat_selector.setValue(1)

        self.capture_button = QPushButton("Capture Visible Task")
        self.capture_button.clicked.connect(self._capture_visible_task)

        control_row.addWidget(QLabel("Type:"))
        control_row.addWidget(self.type_selector)
        control_row.addWidget(QLabel("Search:"))
        control_row.addWidget(self.search_input)
        control_row.addWidget(QLabel("Repeat:"))
        control_row.addWidget(self.repeat_selector)
        control_row.addStretch()
        control_row.addWidget(self.capture_button)

        self.table = QTableWidget(0, 9, self)
        self.table.setHorizontalHeaderLabels([
            "Type",
            "Name",
            "ID",
            "X",
            "Y",
            "Duration",
            "Walk Time",
            "Updated",
            "Action",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addLayout(control_row)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        self.table.setRowCount(0)
        records = self._load_records()
        query = self.search_input.text().strip().lower()
        record_type = self.type_selector.currentText().lower()
        filtered = []

        for record in records:
            text = " ".join(
                [
                    record.type,
                    getattr(record, "name", ""),
                    getattr(record, "town_name", ""),
                    str(getattr(record, "job_id", "")),
                    str(getattr(record, "unit_id", "")),
                ]
            ).lower()
            if query and query not in text:
                continue
            if record_type == "jobs" and record.type != "job":
                continue
            if record_type == "towns" and record.type != "town":
                continue
            filtered.append(record)

        for index, record in enumerate(filtered):
            self._fill_row(index, record)

    def _load_records(self) -> List[Any]:
        return sorted(self.database_manager.list_all(), key=lambda record: getattr(record, "updated_at", ""), reverse=True)

    def _fill_row(self, row: int, record: Any) -> None:
        identifier = str(getattr(record, "job_id", getattr(record, "unit_id", "")))
        values = [
            record.type,
            getattr(record, "name", getattr(record, "town_name", "")),
            identifier,
            str(getattr(record, "x", "")),
            str(getattr(record, "y", "")),
            str(getattr(record, "duration", "-")) if record.type == "job" else "-",
            str(getattr(record, "walk_time_seconds", "-")) if record.type == "town" else "-",
            getattr(record, "updated_at", ""),
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, record)
            self.table.setItem(row, col, item)

        button = QPushButton("ADD TO QUEUE")
        button.clicked.connect(lambda _, payload=record: self._add_record_to_queue(payload))
        self.table.setCellWidget(row, 8, button)

    def _add_record_to_queue(self, record: Any) -> None:
        repeat_count = self.repeat_selector.value()
        if record.type == "job":
            payload = {
                "jobId": int(record.job_id),
                "x": int(record.x),
                "y": int(record.y),
                "duration": int(record.duration),
            }
            task_type = TaskType.JOB
        else:
            payload = {
                "unitId": int(record.unit_id),
                "x": int(record.x),
                "y": int(record.y),
            }
            task_type = TaskType.TOWN

        task = TaskModel(
            type=task_type,
            name=getattr(record, "name", getattr(record, "town_name", "Learned Action")),
            payload=payload,
            remaining=repeat_count,
            repeat_count=repeat_count,
        )
        self.queue_manager.add_task(task)
        self.logger.info("Added learned record to queue: %s", task.name)

    def _capture_visible_task(self) -> None:
        payload = self.browser_manager.extract_current_task_window()
        if not payload:
            return
        if payload.get("type") == "job" and payload.get("jobId"):
            record = JobRecord(
                job_id=int(payload["jobId"]),
                name=payload.get("name") or f"Job {payload.get('jobId')}",
                x=int(payload.get("x") or 0),
                y=int(payload.get("y") or 0),
                duration=int(payload.get("duration") or 15),
            )
            self.database_manager.upsert_job(record)
            self.logger.info("Manually captured job: %s", record.name)
        elif payload.get("type") in {"town", "walk"} and payload.get("unitId"):
            record = TownRecord(
                unit_id=int(payload["unitId"]),
                town_name=payload.get("name") or f"Town {payload.get('unitId')}",
                x=int(payload.get("x") or 0),
                y=int(payload.get("y") or 0),
                walk_time_seconds=None,
            )
            self.database_manager.upsert_town(record)
            self.logger.info("Manually captured town: %s", record.town_name)
        self.refresh()
