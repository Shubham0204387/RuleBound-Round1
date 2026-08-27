from typing import List, Optional

from app.layout import placement
from app.layout.geometry import Rectangle
from app.layout.models import (
    Layout,
    Placement,
    RepairOption,
    Violation,
)
from app.layout.placement import (
    get_product_footprint,
    placement_inside_room,
    placement_overlap_area,
    placement_overlaps,
)
from app.layout.zones import Zone, build_zones


# ============================================================
# RULE CONSTANTS
# ============================================================

WALKWAY_CLEARANCE_MM = 900
EGRESS_CLEARANCE_MM = 1100
DOOR_SWING_CLEARANCE_MM = 850

DESK_REAR_CLEARANCE_MM = 900
CHAIR_PULL_OUT_MM = 750

WALL_OFFSET_MM = 100


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def _zone_rectangle(
    zone: Zone,
) -> Rectangle:

    return Rectangle(
        x_mm=zone.x_mm,
        y_mm=zone.y_mm,
        width_mm=zone.width_mm,
        depth_mm=zone.depth_mm,
    )


def _product_family(
    placement: Placement,
    catalog,
) -> Optional[str]:

    product = catalog.get(
        placement.sku
    )

    if product is None:
        return None

    return product.family


def _wall_offset(
    placement: Placement,
    room,
    catalog,
) -> float:

    footprint = get_product_footprint(
        placement,
        catalog,
    )

    min_x = min(
        point[0]
        for point in room.boundary_mm
    )

    max_x = max(
        point[0]
        for point in room.boundary_mm
    )

    min_y = min(
        point[1]
        for point in room.boundary_mm
    )

    max_y = max(
        point[1]
        for point in room.boundary_mm
    )

    return min(
        footprint.left - min_x,
        max_x - footprint.right,
        footprint.bottom - min_y,
        max_y - footprint.top,
    )


def _zone_overlap_area(
    placement: Placement,
    zone: Zone,
    catalog,
) -> float:

    footprint = get_product_footprint(
        placement,
        catalog,
    )

    return footprint.overlap_area(
        _zone_rectangle(zone)
    )


# ============================================================
# RESTRICTED ZONE VALIDATION
# ============================================================

def _restricted_zone_violation(
    placement: Placement,
    zone: Zone,
    catalog,
    rule_id: str,
    message: str,
    required_value: int,
    violation_id: str,
) -> Optional[Violation]:

    overlap_area = _zone_overlap_area(
        placement,
        zone,
        catalog,
    )

    if overlap_area <= 0:
        return None

    return Violation(
        violation_id=violation_id,
        rule_id=rule_id,
        message=message,
        affected_placement_ids=[
            placement.placement_id
        ],
        measured={
            "intersection_area_mm2":
                overlap_area,
            "zone_id":
                zone.zone_id,
        },
        required={
            "clearance_mm":
                required_value
        },
        repair_options=[
            RepairOption(
                action="move",
                description=(
                    "Move the placement outside "
                    f"the {zone.zone_type}."
                ),
                score=0.9,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                },
            )
        ],
    )


# ============================================================
# RB-GEO-007
# INSIDE ROOM
# ============================================================

def _validate_inside_room(
    placement: Placement,
    room,
    catalog,
    violation_id: str,
) -> Optional[Violation]:

    if placement_inside_room(
        placement,
        room,
        catalog,
    ):
        return None

    return Violation(
        violation_id=violation_id,
        rule_id="RB-GEO-007",
        message=(
            "Every placement footprint must "
            "remain inside the room polygon."
        ),
        affected_placement_ids=[
            placement.placement_id
        ],
        measured={
            "inside_room": False
        },
        required={
            "inside_room": True
        },
        repair_options=[
            RepairOption(
                action="move",
                description=(
                    "Move the placement fully "
                    "inside the room boundary."
                ),
                score=0.95,
                parameters={
                    "placement_id":
                        placement.placement_id,
                },
            )
        ],
    )


# ============================================================
# RB-GEO-005
# WALL OFFSET
# ============================================================

def _validate_wall_offset(
    placement: Placement,
    room,
    catalog,
    violation_id: str,
) -> Optional[Violation]:

    offset = _wall_offset(
        placement,
        room,
        catalog,
    )

    if offset >= WALL_OFFSET_MM:
        return None

    return Violation(
        violation_id=violation_id,
        rule_id="RB-GEO-005",
        message=(
            "Furniture must remain at least "
            "100 mm from a wall unless "
            "wall-mounted."
        ),
        affected_placement_ids=[
            placement.placement_id
        ],
        measured={
            "wall_offset_mm":
                max(0, offset)
        },
        required={
            "wall_offset_mm":
                WALL_OFFSET_MM
        },
        repair_options=[
            RepairOption(
                action="move_from_wall",
                description=(
                    "Move the placement at least "
                    "100 mm away from the nearest wall."
                ),
                score=0.9,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "minimum_offset_mm":
                        WALL_OFFSET_MM,
                },
            )
        ],
    )


# ============================================================
# RB-GEO-006
# NO OVERLAP
# ============================================================

def _validate_overlap(
    first: Placement,
    second: Placement,
    catalog,
    violation_id: str,
) -> Optional[Violation]:

    if not placement_overlaps(
        first,
        second,
        catalog,
    ):
        return None

    overlap_area = placement_overlap_area(
        first,
        second,
        catalog,
    )

    return Violation(
        violation_id=violation_id,
        rule_id="RB-GEO-006",
        message=(
            "Furniture footprints may not overlap."
        ),
        affected_placement_ids=[
            first.placement_id,
            second.placement_id,
        ],
        measured={
            "overlap_mm2":
                overlap_area
        },
        required={
            "overlap_mm2":
                0
        },
        repair_options=[
            RepairOption(
                action="move",
                description=(
                    "Move the second placement "
                    "300 mm east."
                ),
                score=0.85,
                parameters={
                    "placement_id":
                        second.placement_id,
                    "dx_mm":
                        300,
                    "dy_mm":
                        0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the second placement "
                    "300 mm north."
                ),
                score=0.8,
                parameters={
                    "placement_id":
                        second.placement_id,
                    "dx_mm":
                        0,
                    "dy_mm":
                        300,
                },
            ),
        ],
    )


# ============================================================
# CLEARANCE HELPER
# ============================================================

def _axis_clearance(
    first: Placement,
    second: Placement,
    catalog,
) -> float:

    first_rect = get_product_footprint(
        first,
        catalog,
    )

    second_rect = get_product_footprint(
        second,
        catalog,
    )

    horizontal = max(
        second_rect.left - first_rect.right,
        first_rect.left - second_rect.right,
        0,
    )

    vertical = max(
        second_rect.bottom - first_rect.top,
        first_rect.bottom - second_rect.top,
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
# RB-GEO-004
# DESK ↔ CHAIR REAR CLEARANCE
# ============================================================

def _validate_desk_rear_clearance(
    placement: Placement,
    placements: List[Placement],
    catalog,
    violation_id: str,
) -> Optional[Violation]:

    # RB-GEO-004 applies only to desks.
    if _product_family(
        placement,
        catalog,
    ) != "desk":
        return None

    for other in placements:

        # Never compare the placement with itself.
        if (
            other.placement_id
            == placement.placement_id
        ):
            continue

        # IMPORTANT:
        # The 900 mm occupied-desk clearance
        # is checked against task chairs only.
        #
        # We do NOT check:
        # desk ↔ desk
        # desk ↔ storage
        # desk ↔ collaboration
        # desk ↔ accessory
        if (
            _product_family(
                other,
                catalog,
            )
            != "chair"
        ):
            continue

        # Only validate the chair assigned to this desk.
        if other.paired_desk_id != placement.placement_id:
            continue

        clearance = _axis_clearance(
            placement,
            other,
            catalog,
        )

        if clearance >= DESK_REAR_CLEARANCE_MM:
            continue

        first_rect = get_product_footprint(
            placement,
            catalog,
        )

        second_rect = get_product_footprint(
            other,
            catalog,
        )

        # Overlap is handled separately
        # by RB-GEO-006.
        if first_rect.overlaps(
            second_rect
        ):
            continue

        return Violation(
            violation_id=violation_id,
            rule_id="RB-GEO-004",
            message=(
                "Occupied desks require "
                "900 mm rear clearance "
                "from task chairs."
            ),
            affected_placement_ids=[
                placement.placement_id,
                other.placement_id,
            ],
            measured={
                "clearance_mm":
                    clearance
            },
            required={
                "clearance_mm":
                    DESK_REAR_CLEARANCE_MM
            },
            repair_options=[
                RepairOption(
                    action="move",
                    description=(
                        "Move the desk or chair "
                        "to provide 900 mm "
                        "rear clearance."
                    ),
                    score=0.85,
                    parameters={
                        "placement_id":
                            placement.placement_id,
                        "required_clearance_mm":
                            DESK_REAR_CLEARANCE_MM,
                    },
                )
            ],
        )

    return None


# ============================================================
# RB-GEO-008
# CHAIR PULL-OUT CLEARANCE
# ============================================================

def _validate_chair_pull_out(
    placement: Placement,
    placements: List[Placement],
    catalog,
    violation_id: str,
) -> Optional[Violation]:

    # This rule applies only to chairs.
    if _product_family(
        placement,
        catalog,
    ) != "chair":
        return None

    for other in placements:

        # Chair pull-out clearance is checked
        # against desks only.
        if (
            _product_family(
                other,
                catalog,
            )
            != "desk"
        ):
            continue

        # Only validate this chair against its assigned desk.
        if placement.paired_desk_id != other.placement_id:
            continue

        clearance = _axis_clearance(
            placement,
            other,
            catalog,
        )

        if clearance >= CHAIR_PULL_OUT_MM:
            continue

        chair_rect = get_product_footprint(
            placement,
            catalog,
        )

        desk_rect = get_product_footprint(
            other,
            catalog,
        )

        # Overlap is handled separately
        # by RB-GEO-006.
        if chair_rect.overlaps(
            desk_rect
        ):
            continue

        return Violation(
            violation_id=violation_id,
            rule_id="RB-GEO-008",
            message=(
                "Task chairs require a "
                "750 mm pull-out zone."
            ),
            affected_placement_ids=[
                placement.placement_id,
                other.placement_id,
            ],
            measured={
                "clearance_mm":
                    clearance
            },
            required={
                "clearance_mm":
                    CHAIR_PULL_OUT_MM
            },
            repair_options=[
                RepairOption(
                    action="move",
                    description=(
                        "Move the chair to provide "
                        "a 750 mm pull-out zone."
                    ),
                    score=0.85,
                    parameters={
                        "placement_id":
                            placement.placement_id,
                        "required_clearance_mm":
                            CHAIR_PULL_OUT_MM,
                    },
                )
            ],
        )

    return None


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_layout(
    layout: Layout,
    room,
    catalog,
) -> Layout:

    zones = build_zones(room)

    violations = []

    violation_counter = 1

    def add_violation(
        violation: Violation,
    ):

        nonlocal violation_counter

        violation.violation_id = (
            f"V-{violation_counter:04d}"
        )

        violations.append(
            violation
        )

        violation_counter += 1

    # --------------------------------------------------------
    # Validate every placement individually
    # --------------------------------------------------------

    for placement in layout.placements:

        # RB-GEO-007
        violation = _validate_inside_room(
            placement,
            room,
            catalog,
            "TEMP",
        )

        if violation:
            add_violation(
                violation
            )

        # RB-GEO-005
        violation = _validate_wall_offset(
            placement,
            room,
            catalog,
            "TEMP",
        )

        if violation:
            add_violation(
                violation
            )

        # ----------------------------------------------------
        # RB-GEO-001
        # Walkway
        # ----------------------------------------------------

        for zone in zones["walkway"]:

            violation = _restricted_zone_violation(
                placement=placement,
                zone=zone,
                catalog=catalog,
                rule_id="RB-GEO-001",
                message=(
                    "Primary walkways require "
                    "900 mm clear width."
                ),
                required_value=WALKWAY_CLEARANCE_MM,
                violation_id="TEMP",
            )

            if violation:

                add_violation(
                    violation
                )

                break

        # ----------------------------------------------------
        # RB-GEO-002
        # Egress
        # ----------------------------------------------------

        for zone in zones["egress"]:

            violation = _restricted_zone_violation(
                placement=placement,
                zone=zone,
                catalog=catalog,
                rule_id="RB-GEO-002",
                message=(
                    "The marked egress path "
                    "requires 1100 mm clear width."
                ),
                required_value=EGRESS_CLEARANCE_MM,
                violation_id="TEMP",
            )

            if violation:

                add_violation(
                    violation
                )

                break

        # ----------------------------------------------------
        # RB-GEO-003
        # Door swing
        # ----------------------------------------------------

        for zone in zones["doors"]:

            violation = _restricted_zone_violation(
                placement=placement,
                zone=zone,
                catalog=catalog,
                rule_id="RB-GEO-003",
                message=(
                    "No furniture may enter "
                    "the door-swing clearance zone."
                ),
                required_value=DOOR_SWING_CLEARANCE_MM,
                violation_id="TEMP",
            )

            if violation:

                add_violation(
                    violation
                )

                break

        # ----------------------------------------------------
        # RB-GEO-004
        # Desk ↔ Chair
        # ----------------------------------------------------

        violation = _validate_desk_rear_clearance(
            placement,
            layout.placements,
            catalog,
            "TEMP",
        )

        if violation:

            add_violation(
                violation
            )

        # ----------------------------------------------------
        # RB-GEO-008
        # Chair ↔ Desk
        # ----------------------------------------------------

        violation = _validate_chair_pull_out(
            placement,
            layout.placements,
            catalog,
            "TEMP",
        )

        if violation:

            add_violation(
                violation
            )

    # --------------------------------------------------------
    # RB-GEO-006
    # Check every pair for physical overlap
    # --------------------------------------------------------

    for index, first in enumerate(
        layout.placements
    ):

        for second in layout.placements[
            index + 1:
        ]:

            violation = _validate_overlap(
                first,
                second,
                catalog,
                "TEMP",
            )

            if violation:

                add_violation(
                    violation
                )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    layout.violations = violations

    if violations:

        layout.status = "invalid"

    else:

        layout.status = "valid"

    return layout