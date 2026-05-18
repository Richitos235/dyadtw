from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskType(str, Enum):
    JOB = "job"
    TOWN = "town"
    EQUIP = "equip"


@dataclass
class TaskModel:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.JOB
    name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    status: TaskStatus = TaskStatus.PENDING
    repeat_count: int = 1
    remaining: int = 1
    attempts: int = 0
    max_retries: int = 2
    cooldown_seconds: int = 4
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_error: Optional[str] = None

    def mark_updated(self) -> None:
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskModel":
        if "type" not in payload or "name" not in payload:
            raise ValueError("Invalid task payload")
        return cls(
            task_id=payload.get("task_id", str(uuid.uuid4())),
            type=TaskType(payload["type"]),
            name=payload["name"],
            payload=payload.get("payload", {}),
            priority=int(payload.get("priority", 50)),
            status=TaskStatus(payload.get("status", TaskStatus.PENDING)),
            repeat_count=int(payload.get("repeat_count", 1)),
            remaining=int(payload.get("remaining", payload.get("repeat_count", 1))),
            attempts=int(payload.get("attempts", 0)),
            max_retries=int(payload.get("max_retries", 2)),
            cooldown_seconds=int(payload.get("cooldown_seconds", 4)),
            created_at=payload.get("created_at", datetime.utcnow().isoformat()),
            updated_at=payload.get("updated_at", datetime.utcnow().isoformat()),
            last_error=payload.get("last_error"),
        )
