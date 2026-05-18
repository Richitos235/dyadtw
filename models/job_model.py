from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class JobRecord:
    job_id: int
    name: str
    x: int
    y: int
    duration: int
    created_at: str = ""
    updated_at: str = ""
    type: str = "job"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "job_id": self.job_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "duration": self.duration,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "JobRecord":
        return cls(
            job_id=row["job_id"],
            name=row["name"],
            x=row["x"],
            y=row["y"],
            duration=row["duration"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
