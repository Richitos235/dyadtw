from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class JobLog:
    jobId: int
    x: int
    y: int
    duration: int
    taskType: str
    name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobLog":
        return cls(
            jobId=int(data.get("jobId", 0)),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            duration=int(data.get("duration", 15)),
            taskType=str(data.get("taskType", "job")),
            name=data.get("name"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )