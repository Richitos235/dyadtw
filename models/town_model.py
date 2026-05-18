from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TownRecord:
    unit_id: int
    town_name: str
    x: int
    y: int
    walk_time_seconds: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
    type: str = "town"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "unit_id": self.unit_id,
            "town_name": self.town_name,
            "x": self.x,
            "y": self.y,
            "walk_time_seconds": self.walk_time_seconds,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "TownRecord":
        return cls(
            unit_id=row["unit_id"],
            town_name=row["town_name"],
            x=row["x"],
            y=row["y"],
            walk_time_seconds=row["walk_time_seconds"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
