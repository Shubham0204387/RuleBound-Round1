from dataclasses import dataclass
from typing import List, Tuple

from app.layout.models import Placement


@dataclass(frozen=True)
class PlacementPreference:
    family: str
    preferred_zones: List[str]
    avoid_zones: List[str]
    priority: int


FAMILY_STRATEGIES = {
    "desk": PlacementPreference(
        family="desk",
        preferred_zones=[
            "work_zone",
            "perimeter",
            "daylight_zone",
        ],
        avoid_zones=[
            "egress",
            "door_swing",
            "main_circulation",
        ],
        priority=1,
    ),
    "chair": PlacementPreference(
        family="chair",
        preferred_zones=[
            "desk_associated",
            "table_associated",
        ],
        avoid_zones=[
            "egress",
            "door_swing",
            "main_circulation",
        ],
        priority=2,
    ),
    "collaboration": PlacementPreference(
        family="collaboration",
        preferred_zones=[
            "collaboration_zone",
            "open_zone",
        ],
        avoid_zones=[
            "egress",
            "door_swing",
            "window_protection_zone",
        ],
        priority=3,
    ),
    "storage": PlacementPreference(
        family="storage",
        preferred_zones=[
            "perimeter",
            "storage_zone",
        ],
        avoid_zones=[
            "egress",
            "door_swing",
            "main_circulation",
            "window_protection_zone",
        ],
        priority=4,
    ),
    "accessory": PlacementPreference(
        family="accessory",
        preferred_zones=[
            "perimeter",
            "accessory_zone",
            "available_zone",
        ],
        avoid_zones=[
            "egress",
            "door_swing",
            "main_circulation",
        ],
        priority=5,
    ),
}


def get_strategy(
    family: str,
) -> PlacementPreference:

    if family in FAMILY_STRATEGIES:
        return FAMILY_STRATEGIES[family]

    return PlacementPreference(
        family=family,
        preferred_zones=["available_zone"],
        avoid_zones=[
            "egress",
            "door_swing",
            "main_circulation",
        ],
        priority=10,
    )


def get_placement_order(
    families: List[str],
) -> List[str]:

    unique_families = list(
        dict.fromkeys(families)
    )

    return sorted(
        unique_families,
        key=lambda family: (
            get_strategy(family).priority,
            family,
        ),
    )


def preferred_rotations(
    family: str,
) -> List[int]:

    if family == "desk":
        return [0, 180, 90, 270]

    if family == "collaboration":
        return [0, 180, 90, 270]

    if family == "storage":
        return [0, 90, 180, 270]

    if family == "chair":
        return [0, 180, 90, 270]

    return [0, 90, 180, 270]


def placement_score(
    family: str,
    zone: str,
    blocked: bool = False,
) -> float:

    strategy = get_strategy(family)

    if blocked:
        return float("-inf")

    if zone in strategy.preferred_zones:
        index = strategy.preferred_zones.index(
            zone
        )

        return 1.0 - (
            index * 0.15
        )

    if zone in strategy.avoid_zones:
        return -1.0

    return 0.25


def choose_best_rotation(
    family: str,
    available_rotations: List[int],
) -> int:

    preferred = preferred_rotations(
        family
    )

    for rotation in preferred:
        if rotation in available_rotations:
            return rotation

    return available_rotations[0]


def strategy_summary() -> List[str]:

    result = []

    for family in sorted(
        FAMILY_STRATEGIES
    ):
        strategy = FAMILY_STRATEGIES[
            family
        ]

        result.append(
            (
                f"{family}: "
                f"preferred={strategy.preferred_zones}; "
                f"avoid={strategy.avoid_zones}; "
                f"priority={strategy.priority}"
            )
        )

    return result