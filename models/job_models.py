from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class JobDefinition:
    name: str
    jobId: int
    x: int
    y: int
    durations: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "jobId": self.jobId,
            "x": self.x,
            "y": self.y,
            "durations": self.durations,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "JobDefinition":
        return cls(
            name=str(raw["name"]),
            jobId=int(raw["jobId"]),
            x=int(raw["x"]),
            y=int(raw["y"]),
            durations={
                key: int(value)
                for key, value in raw.get("durations", {}).items()
            },
        )
