import threading
from collections import deque
from datetime import datetime
from typing import Callable, Deque, List, Optional

from models.task_models import TaskModel, TaskStatus
from core.storage_manager import StorageManager


class QueueManager:
    def __init__(self, storage: StorageManager, logger) -> None:
        self._lock = threading.RLock()
        self._tasks: Deque[TaskModel] = deque()
        self._listeners: List[Callable[[], None]] = []
        self._event = threading.Event()
        self.logger = logger
        self.storage = storage
        self._load_persisted_queue()

    def _load_persisted_queue(self) -> None:
        tasks = self.storage.load_queue()
        for task in tasks:
            if task.status != TaskStatus.COMPLETED:
                self._tasks.append(task)
        self.logger.debug("Loaded %d persisted tasks from storage", len(self._tasks))

    def _persist(self) -> None:
        self.storage.save_queue(list(self._tasks))

    def _notify(self) -> None:
        self._event.set()
        for listener in list(self._listeners):
            try:
                listener()
            except Exception as error:
                self.logger.exception("Queue listener failed: %s", error)

    def register_listener(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def add_task(self, task: TaskModel) -> None:
        with self._lock:
            if len(self._tasks) >= self.storage.config.get("scheduler", {}).get("max_queue_length", 50):
                self.logger.warning("Attempted to add task while queue is at capacity")
                return
            self._tasks.append(task)
            self.logger.info("Task added to queue: %s", task.name)
            self._persist()
            self._notify()

    def remove_task(self, task_id: str) -> None:
        with self._lock:
            self._tasks = deque([task for task in self._tasks if task.task_id != task_id])
            self.logger.info("Task removed from queue: %s", task_id)
            self._persist()
            self._notify()

    def reorder_task(self, task_id: str, new_index: int) -> None:
        with self._lock:
            tasks = list(self._tasks)
            for current_index, task in enumerate(tasks):
                if task.task_id == task_id:
                    tasks.insert(max(0, min(new_index, len(tasks) - 1)), tasks.pop(current_index))
                    self._tasks = deque(tasks)
                    self.logger.debug("Task %s moved to position %d", task_id, new_index)
                    self._persist()
                    self._notify()
                    return

    def get_next_task(self) -> Optional[TaskModel]:
        with self._lock:
            for task in self._tasks:
                if task.status == TaskStatus.PENDING and task.remaining > 0:
                    return task
            return None

    def get_tasks(self) -> List[TaskModel]:
        with self._lock:
            return list(self._tasks)

    def update_task(self, task_id: str, **kwargs) -> None:
        with self._lock:
            for task in self._tasks:
                if task.task_id == task_id:
                    for key, value in kwargs.items():
                        setattr(task, key, value)
                    task.mark_updated()
                    self.logger.debug("Task updated: %s (%s)", task_id, kwargs)
                    break
            self._persist()
            self._notify()

    def pause_task(self, task_id: str) -> None:
        self.update_task(task_id, status=TaskStatus.PAUSED)

    def resume_task(self, task_id: str) -> None:
        self.update_task(task_id, status=TaskStatus.PENDING)

    def mark_task_completed(self, task_id: str) -> None:
        self.update_task(task_id, status=TaskStatus.COMPLETED, remaining=0)

    def mark_task_failed(self, task_id: str, error_message: str) -> None:
        self.update_task(task_id, status=TaskStatus.FAILED, last_error=error_message)

    def wait_for_update(self, timeout: float) -> bool:
        result = self._event.wait(timeout)
        self._event.clear()
        return result

    def clear_completed(self) -> None:
        with self._lock:
            self._tasks = deque([task for task in self._tasks if task.status != TaskStatus.COMPLETED])
            self._persist()
            self._notify()
