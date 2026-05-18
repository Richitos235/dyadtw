import json
import random
import threading
import time
from typing import Any, Dict, List, Optional

from core.browser_manager import BrowserManager
from core.injector_manager import InjectorManager
from core.queue_manager import QueueManager
from core.storage_manager import StorageManager
from models.task_models import TaskModel, TaskStatus, TaskType


class TaskExecutor:
    def __init__(
        self,
        queue_manager: QueueManager,
        browser_manager: BrowserManager,
        injector_manager: InjectorManager,
        storage: StorageManager,
        logger,
    ) -> None:
        self.queue_manager = queue_manager
        self.browser_manager = browser_manager
        self.injector_manager = injector_manager
        self.storage = storage
        self.logger = logger
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.queue_manager.register_listener(self._wake)

    def start(self) -> None:
        if self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread.start()
        self.logger.info("Task executor started")

    def stop(self) -> None:
        self._stop_event.set()
        self.logger.info("Task executor stopping")

    def _wake(self) -> None:
        self._wake_event.set()

    def _ensure_wake_event(self) -> None:
        if not hasattr(self, "_wake_event"):
            self._wake_event = threading.Event()

    def _run(self) -> None:
        self._ensure_wake_event()
        interval = float(self.storage.config.get("scheduler", {}).get("poll_interval_seconds", 2))
        while not self._stop_event.wait(0):
            self._process_injected_jobs()
            task = self.queue_manager.get_next_task()
            if task is None:
                self._wake_event.wait(interval)
                self._wake_event.clear()
                continue
            if task.status == TaskStatus.PAUSED:
                self._wake_event.wait(interval)
                self._wake_event.clear()
                continue
            self._execute_task(task)
            self._wake_event.wait(interval)
            self._wake_event.clear()

    def _process_injected_jobs(self) -> None:
        if self.browser_manager.driver is None:
            return
        for payload in self.injector_manager.consume_job_events():
            task = self._build_task_from_payload(payload)
            if task is not None:
                self.queue_manager.add_task(task)

    def _build_task_from_payload(self, payload: Dict[str, Any]) -> Optional[TaskModel]:
        if not payload.get("jobId"):
            return None
        task_type = TaskType.JOB if payload.get("action") in {"queue", "start"} else TaskType.JOB
        name = payload.get("name", f"Job {payload.get('jobId')}")
        remaining = int(payload.get("repeat_count", 1))
        return TaskModel(
            type=task_type,
            name=name,
            payload={
                "jobId": int(payload["jobId"]),
                "x": int(payload.get("x", 0)),
                "y": int(payload.get("y", 0)),
                "duration": int(payload.get("duration", 15)),
                "motivation": float(payload.get("motivation", 100)),
            },
            repeat_count=remaining,
            remaining=remaining,
        )

    def _execute_task(self, task: TaskModel) -> None:
        self.logger.info("Executing task %s [%s]", task.name, task.task_id)
        self.queue_manager.update_task(task.task_id, status=TaskStatus.RUNNING)
        try:
            if task.type == TaskType.JOB:
                self._execute_job(task)
            elif task.type == TaskType.TOWN:
                self._execute_town(task)
            elif task.type == TaskType.EQUIP:
                self._execute_equip(task)
            else:
                raise ValueError(f"Unsupported task type: {task.type}")
        except Exception as error:
            self.logger.exception("Task execution failed for %s: %s", task.task_id, error)
            task.attempts += 1
            if task.attempts <= task.max_retries:
                task.status = TaskStatus.PENDING
                task.last_error = str(error)
                self.queue_manager.update_task(task.task_id, status=TaskStatus.PENDING, attempts=task.attempts, last_error=task.last_error)
                self._delay(random.uniform(2.0, 4.0))
                return
            self.queue_manager.mark_task_failed(task.task_id, str(error))
            return
        self._delay(random.uniform(0.8, 1.6))

    def _execute_job(self, task: TaskModel) -> None:
        motivation = self._read_motivation(task.payload.get("jobId"))
        threshold = float(self.storage.config.get("scheduler", {}).get("motivation_threshold", 75))
        if motivation is not None and motivation < threshold:
            self.logger.info("Skipping task %s due to low motivation %.1f", task.name, motivation)
            self.queue_manager.mark_task_completed(task.task_id)
            return

        if not self.browser_manager.driver:
            raise RuntimeError("Browser is not available")

        queue_length = self._read_game_queue_length()
        if queue_length is None or queue_length >= 4:
            self.logger.debug("Server queue full or unavailable (%s), deferring task", queue_length)
            raise RuntimeError("Server queue is busy")

        script = (
            f"TaskQueue.add(new TaskJob({task.payload['jobId']}, {task.payload['x']}, {task.payload['y']}, {task.payload['duration']}));"
        )
        if not self.browser_manager.execute_script(script, fallback=False):
            raise RuntimeError("Failed to queue job")

        task.remaining = max(0, task.remaining - 1)
        if task.remaining == 0:
            self.queue_manager.mark_task_completed(task.task_id)
        else:
            self.queue_manager.update_task(task.task_id, status=TaskStatus.PENDING, remaining=task.remaining)

    def _execute_town(self, task: TaskModel) -> None:
        if not self.browser_manager.driver:
            raise RuntimeError("Browser is not available")

        script = f"TaskQueue.add(new TaskWalk({task.payload['unitId']}, 'town'));"
        if not self.browser_manager.execute_script(script, fallback=False):
            raise RuntimeError("Failed to queue town move")

        travel_time = self._read_current_travel_time() or 0
        self._delay(travel_time + 1)
        self.queue_manager.mark_task_completed(task.task_id)

    def _execute_equip(self, task: TaskModel) -> None:
        if not self.browser_manager.driver:
            raise RuntimeError("Browser is not available")

        script = (
            "Ajax.remoteCall('inventory', 'switch_equip', {"
            f"id: {task.payload['equipId']}, last_inv_id: {task.payload['lastInvId']}" 
            "}, function(json) {});"
        )
        if not self.browser_manager.execute_script(script, fallback=False):
            raise RuntimeError("Failed to switch equipment")

        task.remaining = max(0, task.remaining - 1)
        if task.remaining == 0:
            self.queue_manager.mark_task_completed(task.task_id)
        else:
            self.queue_manager.update_task(task.task_id, status=TaskStatus.PENDING, remaining=task.remaining)

    def _read_motivation(self, job_id: int) -> Optional[float]:
        script = f"return JobWindow.getJob({job_id}) ? JobWindow.getJob({job_id}).motivation : null;"
        motivation = self.browser_manager.execute_script(script, fallback=None)
        if motivation is None:
            return None
        try:
            return float(motivation) * 100.0
        except (TypeError, ValueError):
            return None

    def _read_game_queue_length(self) -> Optional[int]:
        script = "return TaskQueue && TaskQueue.queue ? TaskQueue.queue.length : null;"
        result = self.browser_manager.execute_script(script, fallback=None)
        try:
            return int(result) if result is not None else None
        except (TypeError, ValueError):
            return None

    def _read_current_travel_time(self) -> Optional[int]:
        script = (
            "var tasks = TaskQueue.queue || [];"
            "for (var i = 0; i < tasks.length; i++) {"
            "  if (tasks[i].data && tasks[i].data.name === 'way') { return tasks[i].data.duration; }"
            "} return null;"
        )
        result = self.browser_manager.execute_script(script, fallback=None)
        try:
            return int(result) if result is not None else None
        except (TypeError, ValueError):
            return None

    def _delay(self, seconds: float) -> None:
        multiplier = float(self.storage.config.get("browser", {}).get("delay_multiplier", 1.0))
        time.sleep(max(0.1, seconds * multiplier))
