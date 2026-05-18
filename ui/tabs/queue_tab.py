from typing import Optional

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

from core.queue_manager import QueueManager
from models.task_models import TaskModel, TaskStatus


class QueueTab(QWidget):
    def __init__(self, queue_manager: QueueManager, logger) -> None:
        super().__init__()
        self.queue_manager = queue_manager
        self.logger = logger
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Status", "Remaining", "Priority", "Last Error"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        controls = QHBoxLayout()
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_selected)
        self.pause_button = QPushButton("Pause/Resume")
        self.pause_button.clicked.connect(self._toggle_selected)
        self.up_button = QPushButton("Move Up")
        self.up_button.clicked.connect(lambda: self._move_selected(-1))
        self.down_button = QPushButton("Move Down")
        self.down_button.clicked.connect(lambda: self._move_selected(1))

        controls.addWidget(QLabel("Queue Management:"))
        controls.addWidget(self.remove_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.up_button)
        controls.addWidget(self.down_button)

        layout.addLayout(controls)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        tasks = self.queue_manager.get_tasks()
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self._set_row(row, task)

    def _set_row(self, row: int, task: TaskModel) -> None:
        values = [
            task.name,
            task.type.value,
            task.status.value,
            str(task.remaining),
            str(task.priority),
            task.last_error or "",
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, task.task_id)
            self.table.setItem(row, col, item)

    def _selected_task_id(self) -> Optional[str]:
        selected = self.table.selectedItems()
        if not selected:
            return None
        return selected[0].data(Qt.UserRole)

    def _remove_selected(self) -> None:
        task_id = self._selected_task_id()
        if task_id:
            self.queue_manager.remove_task(task_id)
            self.refresh()

    def _toggle_selected(self) -> None:
        task_id = self._selected_task_id()
        if not task_id:
            return
        for task in self.queue_manager.get_tasks():
            if task.task_id == task_id:
                if task.status == TaskStatus.PAUSED:
                    self.queue_manager.resume_task(task_id)
                elif task.status == TaskStatus.PENDING:
                    self.queue_manager.pause_task(task_id)
                break
        self.refresh()

    def _move_selected(self, direction: int) -> None:
        task_id = self._selected_task_id()
        if not task_id:
            return
        tasks = self.queue_manager.get_tasks()
        for index, task in enumerate(tasks):
            if task.task_id == task_id:
                new_index = max(0, min(len(tasks) - 1, index + direction))
                self.queue_manager.reorder_task(task_id, new_index)
                self.refresh()
                return
