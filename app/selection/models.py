from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CandidateCheck:
    name: str
    passed: bool
    reason: str


@dataclass
class ProductCandidate:
    sku: str
    family: str
    name: str
    quantity: Optional[int]

    list_price_inr: int
    labour_minutes: int
    lead_time_days: int

    compatible_finish_ids: List[str] = field(
        default_factory=list
    )

    historical_quantity: int = 0

    checks: List[CandidateCheck] = field(
        default_factory=list
    )

    evidence: List[str] = field(
        default_factory=list
    )


@dataclass
class CandidateSet:
    room_id: str
    family: str
    quantity: Optional[int]

    quantity_status: str

    candidates: List[ProductCandidate] = field(
        default_factory=list
    )

    rejected: List[Dict] = field(
        default_factory=list
    )