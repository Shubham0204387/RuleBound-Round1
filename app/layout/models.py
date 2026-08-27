from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Placement:
    placement_id: str
    sku: str
    finish_id: str
    x_mm: int
    y_mm: int
    rotation_deg: int = 0
    paired_desk_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "placement_id": self.placement_id,
            "sku": self.sku,
            "finish_id": self.finish_id,
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
            "rotation_deg": self.rotation_deg,
            "paired_desk_id": self.paired_desk_id,
        }


@dataclass
class RepairOption:
    action: str
    description: str
    score: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "action": self.action,
            "description": self.description,
        }

        if self.score is not None:
            data["score"] = self.score

        if self.parameters:
            data["parameters"] = self.parameters

        return data


@dataclass
class Violation:
    violation_id: str
    rule_id: str
    message: str
    affected_placement_ids: List[str] = field(default_factory=list)
    measured: Dict[str, Any] = field(default_factory=dict)
    required: Dict[str, Any] = field(default_factory=dict)
    repair_options: List[RepairOption] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "rule_id": self.rule_id,
            "message": self.message,
            "affected_placement_ids": self.affected_placement_ids,
            "measured": self.measured,
            "required": self.required,
            "repair_options": [
                option.to_dict()
                for option in self.repair_options
            ],
        }


@dataclass
class Layout:
    room_id: str
    placements: List[Placement] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    status: str = "invalid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "placements": [
                placement.to_dict()
                for placement in self.placements
            ],
            "violations": [
                violation.to_dict()
                for violation in self.violations
            ],
            "status": self.status,
        }

    def is_valid(self) -> bool:
        return self.status == "valid"

    def is_unsatisfiable(self) -> bool:
        return self.status == "unsatisfiable"