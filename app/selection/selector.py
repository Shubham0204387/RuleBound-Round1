from dataclasses import dataclass, field
from typing import List, Optional

from app.resolution.models import (
    ResolvedFurnitureRequirement,
)

from app.selection.candidates import (
    build_candidates,
)

from app.selection.scorer import (
    ScoredCandidate,
    rank_candidates,
    score_candidates,
)


@dataclass
class SelectionResult:
    room_id: str
    family: str
    quantity: Optional[int]
    quantity_status: str

    selected: Optional[ScoredCandidate]

    alternatives: List[
        ScoredCandidate
    ] = field(default_factory=list)

    candidate_count: int = 0


def select_product(
    room_id: str,
    requirement: ResolvedFurnitureRequirement,
    catalog,
    historical_jobs=None,
    requested_finish_ids=None,
    alternative_count: int = 3,
):
    candidate_set = build_candidates(
        room_id=room_id,
        requirement=requirement,
        catalog=catalog,
        historical_jobs=historical_jobs,
        requested_finish_ids=requested_finish_ids,
    )

    scored = score_candidates(
        candidate_set.candidates,
        requested_finish_ids=requested_finish_ids,
    )

    ranked = rank_candidates(
        scored
    )

    selected = (
        ranked[0]
        if ranked
        else None
    )

    alternatives = ranked[
        1:1 + alternative_count
    ]

    return SelectionResult(
        room_id=room_id,
        family=requirement.family,
        quantity=requirement.quantity,
        quantity_status=requirement.quantity_status,
        selected=selected,
        alternatives=alternatives,
        candidate_count=len(
            candidate_set.candidates
        ),
    )