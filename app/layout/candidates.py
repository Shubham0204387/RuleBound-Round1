from dataclasses import dataclass
from typing import List, Optional

from app.layout.models import Placement
from app.layout.placement import (
    create_placement,
    get_product_footprint,
    placement_inside_room,
    placement_overlaps,
)
from app.layout.strategies import (
    placement_score,
    preferred_rotations,
)
from app.layout.zones import Zone


WALL_OFFSET_MM = 100

DESK_CHAIR_CLEARANCE_MM = 900
CHAIR_PULL_OUT_CLEARANCE_MM = 750

PROTECTED_ZONE_TYPES = {
    "egress",
    "walkway",
    "door_swing",
    "window_protection_zone",
}


@dataclass(frozen=True)
class PositionCandidate:
    placement: Placement
    zone_id: str
    zone_type: str
    strategy_score: float


# ============================================================
# BASIC ZONE / GEOMETRY HELPERS
# ============================================================

def zone_contains_footprint(
    zone: Zone,
    placement: Placement,
    catalog,
) -> bool:

    footprint = get_product_footprint(
        placement,
        catalog,
    )

    zone_right = zone.x_mm + zone.width_mm
    zone_top = zone.y_mm + zone.depth_mm

    return (
        footprint.left >= zone.x_mm
        and footprint.right <= zone_right
        and footprint.bottom >= zone.y_mm
        and footprint.top <= zone_top
    )


def generate_grid_points(
    zone: Zone,
    step_mm: int = 300,
):
    if (
        zone.width_mm <= 0
        or zone.depth_mm <= 0
    ):
        return

    x = zone.x_mm

    max_x = zone.x_mm + zone.width_mm
    max_y = zone.y_mm + zone.depth_mm

    while x <= max_x:

        y = zone.y_mm

        while y <= max_y:
            yield x, y
            y += step_mm

        x += step_mm


def _has_wall_offset(
    placement,
    room,
    catalog,
    required_mm=WALL_OFFSET_MM,
):
    footprint = get_product_footprint(
        placement,
        catalog,
    )

    room_min_x = min(
        point[0]
        for point in room.boundary_mm
    )

    room_max_x = max(
        point[0]
        for point in room.boundary_mm
    )

    room_min_y = min(
        point[1]
        for point in room.boundary_mm
    )

    room_max_y = max(
        point[1]
        for point in room.boundary_mm
    )

    return (
        footprint.left - room_min_x >= required_mm
        and room_max_x - footprint.right >= required_mm
        and footprint.bottom - room_min_y >= required_mm
        and room_max_y - footprint.top >= required_mm
    )


def _overlaps_protected_zone(
    placement,
    zone,
    catalog,
):
    footprint = get_product_footprint(
        placement,
        catalog,
    )

    zone_left = zone.x_mm
    zone_right = zone.x_mm + zone.width_mm

    zone_bottom = zone.y_mm
    zone_top = zone.y_mm + zone.depth_mm

    return (
        footprint.left < zone_right
        and footprint.right > zone_left
        and footprint.bottom < zone_top
        and footprint.top > zone_bottom
    )


def _clear_of_protected_zones(
    placement,
    zones,
    catalog,
):
    for zone in zones:

        if zone.zone_type not in PROTECTED_ZONE_TYPES:
            continue

        if _overlaps_protected_zone(
            placement,
            zone,
            catalog,
        ):
            return False

    return True


def _candidate_is_valid(
    placement,
    room,
    zone,
    catalog,
    existing_placements,
    all_zones,
):
    if not placement_inside_room(
        placement,
        room,
        catalog,
    ):
        return False

    if not zone_contains_footprint(
        zone,
        placement,
        catalog,
    ):
        return False

    if not _has_wall_offset(
        placement,
        room,
        catalog,
    ):
        return False

    if not _clear_of_protected_zones(
        placement,
        all_zones,
        catalog,
    ):
        return False

    for existing in existing_placements:

        if placement_overlaps(
            placement,
            existing,
            catalog,
        ):
            return False

    return True


# ============================================================
# GENERAL CANDIDATE GENERATOR
# ============================================================

def generate_candidates(
    room,
    product,
    family: str,
    finish_id: str,
    zones: List[Zone],
    catalog,
    existing_placements: Optional[
        List[Placement]
    ] = None,
    step_mm: int = 300,
    max_candidates: int = 100,
) -> List[PositionCandidate]:

    existing_placements = existing_placements or []

    candidates = []

    preferred_zone_types = {
        "desk": [
            "open_zone",
            "usable_zone",
            "perimeter",
        ],
        "chair": [
            "open_zone",
            "usable_zone",
        ],
        "collaboration": [
            "open_zone",
            "usable_zone",
        ],
        "storage": [
            "perimeter",
            "usable_zone",
        ],
        "accessory": [
            "perimeter",
            "open_zone",
            "usable_zone",
        ],
    }

    family_preferences = preferred_zone_types.get(
        family,
        ["usable_zone"],
    )

    placement_zones = [
        zone
        for zone in zones
        if zone.zone_type not in PROTECTED_ZONE_TYPES
    ]

    ordered_zones = sorted(
        placement_zones,
        key=lambda zone: (
            (
                family_preferences.index(
                    zone.zone_type
                )
                if zone.zone_type in family_preferences
                else 99
            ),
            zone.priority,
            zone.zone_id,
        ),
    )

    rotations = preferred_rotations(family)

    candidate_number = 1

    for zone in ordered_zones:

        if len(candidates) >= max_candidates:
            break

        for rotation in rotations:

            if len(candidates) >= max_candidates:
                break

            for x_mm, y_mm in generate_grid_points(
                zone,
                step_mm,
            ):

                if len(candidates) >= max_candidates:
                    break

                placement = create_placement(
                    placement_id=(
                        f"CAND-{candidate_number:04d}"
                    ),
                    sku=product.sku,
                    finish_id=finish_id,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    rotation_deg=rotation,
                )

                if not _candidate_is_valid(
                    placement,
                    room,
                    zone,
                    catalog,
                    existing_placements,
                    zones,
                ):
                    continue

                score = placement_score(
                    family,
                    zone.zone_type,
                )

                candidates.append(
                    PositionCandidate(
                        placement=placement,
                        zone_id=zone.zone_id,
                        zone_type=zone.zone_type,
                        strategy_score=score,
                    )
                )

                candidate_number += 1

    candidates.sort(
        key=lambda candidate: (
            -candidate.strategy_score,
            candidate.placement.y_mm,
            candidate.placement.x_mm,
            candidate.placement.rotation_deg,
        )
    )

    return candidates


# ============================================================
# CLEARANCE
# ============================================================

def _minimum_axis_clearance(
    first,
    second,
    catalog,
):
    first_fp = get_product_footprint(
        first,
        catalog,
    )

    second_fp = get_product_footprint(
        second,
        catalog,
    )

    horizontal = max(
        second_fp.left - first_fp.right,
        first_fp.left - second_fp.right,
        0,
    )

    vertical = max(
        second_fp.bottom - first_fp.top,
        first_fp.bottom - second_fp.top,
        0,
    )

    if horizontal == 0:
        return vertical

    if vertical == 0:
        return horizontal

    return min(
        horizontal,
        vertical,
    )


# ============================================================
# FLEXIBLE CHAIR POSITIONS
# ============================================================

def _chair_position_candidates(
    desk,
    chair_product,
    catalog,
    step_mm=300,
):
    """
    Generate a broad set of chair positions around the desk.

    Chairs are generated on all four sides and can slide
    continuously along the desk edges.

    The actual clearance and room/zone validation are
    performed later by find_chair_candidates_for_desk().
    """

    desk_fp = get_product_footprint(
        desk,
        catalog,
    )

    chair_width = chair_product.width_mm
    chair_depth = chair_product.depth_mm

    clearance = CHAIR_PULL_OUT_CLEARANCE_MM

    positions = []

    # ========================================================
    # RIGHT SIDE
    # ========================================================

    right_x = (
        desk_fp.right
        + clearance
    )

    y = (
        desk_fp.bottom
        - chair_depth
    )

    while y <= desk_fp.top:

        positions.append(
            (
                right_x,
                y,
            )
        )

        y += step_mm

    # ========================================================
    # LEFT SIDE
    # ========================================================

    left_x = (
        desk_fp.left
        - chair_width
        - clearance
    )

    y = (
        desk_fp.bottom
        - chair_depth
    )

    while y <= desk_fp.top:

        positions.append(
            (
                left_x,
                y,
            )
        )

        y += step_mm

    # ========================================================
    # ABOVE
    # ========================================================

    above_y = (
        desk_fp.top
        + clearance
    )

    x = (
        desk_fp.left
        - chair_width
    )

    while x <= desk_fp.right:

        positions.append(
            (
                x,
                above_y,
            )
        )

        x += step_mm

    # ========================================================
    # BELOW
    # ========================================================

    below_y = (
        desk_fp.bottom
        - chair_depth
        - clearance
    )

    x = (
        desk_fp.left
        - chair_width
    )

    while x <= desk_fp.right:

        positions.append(
            (
                x,
                below_y,
            )
        )

        x += step_mm

    # ========================================================
    # EXTRA SLIDING POSITIONS
    #
    # Generate additional positions slightly farther away.
    # These give the global workstation search more choices
    # when neighbouring desks occupy the primary positions.
    # ========================================================

    for extra_clearance in (
        clearance + step_mm,
        clearance + (2 * step_mm),
    ):

        # RIGHT
        x = (
            desk_fp.right
            + extra_clearance
        )

        y = (
            desk_fp.bottom
            - chair_depth
        )

        while y <= desk_fp.top:

            positions.append(
                (
                    x,
                    y,
                )
            )

            y += step_mm

        # LEFT
        x = (
            desk_fp.left
            - chair_width
            - extra_clearance
        )

        y = (
            desk_fp.bottom
            - chair_depth
        )

        while y <= desk_fp.top:

            positions.append(
                (
                    x,
                    y,
                )
            )

            y += step_mm

        # ABOVE
        y = (
            desk_fp.top
            + extra_clearance
        )

        x = (
            desk_fp.left
            - chair_width
        )

        while x <= desk_fp.right:

            positions.append(
                (
                    x,
                    y,
                )
            )

            x += step_mm

        # BELOW
        y = (
            desk_fp.bottom
            - chair_depth
            - extra_clearance
        )

        x = (
            desk_fp.left
            - chair_width
        )

        while x <= desk_fp.right:

            positions.append(
                (
                    x,
                    y,
                )
            )

            x += step_mm

    # ========================================================
    # Remove duplicate coordinates
    # ========================================================

    unique_positions = list(
        dict.fromkeys(
            positions
        )
    )

    return unique_positions


# ============================================================
# CHAIR CANDIDATES FOR A DESK
# ============================================================

def find_chair_candidates_for_desk(
    room,
    desk,
    chair_product,
    finish_id,
    zones,
    catalog,
    existing_placements=None,
    step_mm=300,
    max_candidates=100,
):
    """
    Generate flexible chair candidates around one desk.

    A chair must:

    - remain inside the room
    - remain inside a valid zone
    - maintain wall offset
    - avoid protected zones
    - avoid existing furniture
    - not overlap the desk
    - maintain 900 mm clearance from the
      associated desk
    - maintain 900 mm clearance from
      every existing desk
    """

    existing_placements = (
        existing_placements or []
    )

    results = []

    candidate_number = 1

    placement_zones = [
        zone
        for zone in zones
        if zone.zone_type not in PROTECTED_ZONE_TYPES
    ]

    existing_desks = [
        existing
        for existing in existing_placements
        if (
            catalog[existing.sku].family
            == "desk"
        )
        and (
            existing.placement_id
            != desk.placement_id
        )
    ]

    positions = _chair_position_candidates(
        desk,
        chair_product,
        catalog,
        step_mm=step_mm,
    )

    rotations = preferred_rotations(
        "chair"
    )

    for x_mm, y_mm in positions:

        if len(results) >= max_candidates:
            break

        for rotation in rotations:

            if len(results) >= max_candidates:
                break

            placement = create_placement(
                placement_id=(
                    f"CAND-CHAIR-{candidate_number:04d}"
                ),
                sku=chair_product.sku,
                finish_id=finish_id,
                x_mm=x_mm,
                y_mm=y_mm,
                rotation_deg=rotation,
            )

            # ------------------------------------------------
            # Room boundary
            # ------------------------------------------------

            if not placement_inside_room(
                placement,
                room,
                catalog,
            ):
                continue

            # ------------------------------------------------
            # Valid placement zone
            # ------------------------------------------------

            matching_zones = [
                zone
                for zone in placement_zones
                if zone_contains_footprint(
                    zone,
                    placement,
                    catalog,
                )
            ]

            if not matching_zones:
                continue

            # ------------------------------------------------
            # Wall offset
            # ------------------------------------------------

            if not _has_wall_offset(
                placement,
                room,
                catalog,
            ):
                continue

            # ------------------------------------------------
            # Protected zones
            # ------------------------------------------------

            if not _clear_of_protected_zones(
                placement,
                zones,
                catalog,
            ):
                continue

            # ------------------------------------------------
            # Associated desk clearance
            # ------------------------------------------------

            if (
                _minimum_axis_clearance(
                    placement,
                    desk,
                    catalog,
                )
                < CHAIR_PULL_OUT_CLEARANCE_MM
            ):
                continue

            # ------------------------------------------------
            # Existing desk clearance
            # ------------------------------------------------

            valid = True

            for existing_desk in existing_desks:

                clearance = (
                    _minimum_axis_clearance(
                        placement,
                        existing_desk,
                        catalog,
                    )
                )

                if (
                    clearance
                    < CHAIR_PULL_OUT_CLEARANCE_MM
                ):
                    valid = False
                    break

            if not valid:
                continue

            # ------------------------------------------------
            # Existing furniture collision
            # ------------------------------------------------

            if any(
                placement_overlaps(
                    placement,
                    existing,
                    catalog,
                )
                for existing
                in existing_placements
            ):
                continue

            # ------------------------------------------------
            # Candidate accepted
            # ------------------------------------------------

            zone = matching_zones[0]

            score = placement_score(
                "chair",
                zone.zone_type,
            )

            results.append(
                PositionCandidate(
                    placement=placement,
                    zone_id=zone.zone_id,
                    zone_type=zone.zone_type,
                    strategy_score=score,
                )
            )

            candidate_number += 1

    # --------------------------------------------------------
    # Prefer candidates with better zone score and then
    # deterministic coordinates.
    # --------------------------------------------------------

    results.sort(
        key=lambda candidate: (
            -candidate.strategy_score,
            candidate.placement.y_mm,
            candidate.placement.x_mm,
            candidate.placement.rotation_deg,
        )
    )

    return results