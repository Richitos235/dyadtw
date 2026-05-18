from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.browser_manager import BrowserManager
from core.injector_manager import InjectorManager
from core.queue_manager import QueueManager
from models.task_models import TaskModel, TaskType


class GameQueueTab(QWidget):
    def __init__(self, queue_manager: QueueManager, browser_manager: BrowserManager, injector_manager: InjectorManager, logger) -> None:
        super().__init__()
        self.queue_manager = queue_manager
        self.browser_manager = browser_manager
        self.injector_manager = injector_manager
        self.logger = logger
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        heading = QLabel("Detected Game Queue and Injected Jobs")
        heading.setAlignment(Qt.AlignCenter)
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Title", "Duration", "Source", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        self.add_button = QPushButton("Add Injected Job")
        self.add_button.clicked.connect(self._add_injected_job)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.add_button)

        layout.addWidget(heading)
        layout.addLayout(controls)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        self.table.setRowCount(0)
        self._populate_game_queue()
        self._populate_injected_jobs()

    def _populate_game_queue(self) -> None:
        rows = self._read_game_queue() or []
        for item in rows:
            self._add_row(item.get("title", "Unknown"), str(item.get("duration", "-")), "server", item.get("status", "active"))

    def _populate_injected_jobs(self) -> None:
        jobs = self.injector_manager.fetch_job_events()
        for item in jobs:
            title = item.get("name", "Unknown")
            duration = f"{item.get('duration', 15)}s"
            self._add_row(title, duration, "injected", item.get("action", "queue"))

    def _add_row(self, title: str, duration: str, source: str, status: str) -> None:
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        self.table.setItem(row_index, 0, QTableWidgetItem(title))
        self.table.setItem(row_index, 1, QTableWidgetItem(duration))
        self.table.setItem(row_index, 2, QTableWidgetItem(source))
        self.table.setItem(row_index, 3, QTableWidgetItem(status))

    def _read_game_queue(self) -> List[dict]:
        script = (
            "return TaskQueue.queue.map(function(t) {"
            "  var title = t.title || (t.data && t.data.name) || 'unnamed';"
            "  return { title: title, duration: t.duration || 0, status: 'active' };"
            "});"
        )
        result = self.browser_manager.execute_script(script, fallback=[])
        if isinstance(result, list):
            return result
        return []

    def _add_injected_job(self) -> None:
        jobs = self.injector_manager.consume_job_events()
        for payload in jobs:
            task = TaskModel(
                type=TaskType.JOB,
                name=payload.get("name", f"Job {payload.get('jobId')}") or "Unknown",
                payload={
                    "jobId": int(payload.get("jobId", 0)),
                    "x": int(payload.get("x", 0)),
                    "y": int(payload.get("y", 0)),
                    "duration": int(payload.get("duration", 15)),
                },
                remaining=int(payload.get("repeat_count", 1)),
            )
            self.queue_manager.add_task(task)
        self.refresh()
