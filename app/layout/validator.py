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

    # --------------------------------------------------------
    # RB-GEO-001
    # Walkway receives executable directional
    # repair vectors.
    # --------------------------------------------------------

    if rule_id == "RB-GEO-001":

        placement_footprint = get_product_footprint(
            placement,
            catalog,
        )

        repair_options = [
            RepairOption(
                action="move",
                description=(
                    "Move the placement left outside "
                    f"the {zone.zone_type}."
                ),
                score=0.90,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.x_mm
                        - placement_footprint.right
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement right outside "
                    f"the {zone.zone_type}."
                ),
                score=0.89,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.right_mm
                        - placement_footprint.left
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement down outside "
                    f"the {zone.zone_type}."
                ),
                score=0.88,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.y_mm
                        - placement_footprint.top
                    ),
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement up outside "
                    f"the {zone.zone_type}."
                ),
                score=0.87,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.bottom_mm
                        - placement_footprint.bottom
                    ),
                },
            ),
        ]

    # --------------------------------------------------------
    # RB-GEO-002
    # Egress receives executable directional
    # repair vectors.
    # --------------------------------------------------------

    elif rule_id == "RB-GEO-002":

        placement_footprint = get_product_footprint(
            placement,
            catalog,
        )

        repair_options = [
            RepairOption(
                action="move",
                description=(
                    "Move the placement left outside "
                    f"the {zone.zone_type}."
                ),
                score=0.90,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.x_mm
                        - placement_footprint.right
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement right outside "
                    f"the {zone.zone_type}."
                ),
                score=0.89,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.right_mm
                        - placement_footprint.left
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement down outside "
                    f"the {zone.zone_type}."
                ),
                score=0.88,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.y_mm
                        - placement_footprint.top
                    ),
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement up outside "
                    f"the {zone.zone_type}."
                ),
                score=0.87,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.bottom_mm
                        - placement_footprint.bottom
                    ),
                },
            ),
        ]

    # --------------------------------------------------------
    # RB-GEO-003
    # Door swing receives executable directional
    # repair vectors.
    # --------------------------------------------------------

    elif rule_id == "RB-GEO-003":

        placement_footprint = get_product_footprint(
            placement,
            catalog,
        )

        repair_options = [
            RepairOption(
                action="move",
                description=(
                    "Move the placement left outside "
                    f"the {zone.zone_type}."
                ),
                score=0.90,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.x_mm
                        - placement_footprint.right
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement right outside "
                    f"the {zone.zone_type}."
                ),
                score=0.89,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": int(
                        zone.right_mm
                        - placement_footprint.left
                    ),
                    "dy_mm": 0,
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement down outside "
                    f"the {zone.zone_type}."
                ),
                score=0.88,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.y_mm
                        - placement_footprint.top
                    ),
                },
            ),
            RepairOption(
                action="move",
                description=(
                    "Move the placement up outside "
                    f"the {zone.zone_type}."
                ),
                score=0.87,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "zone_id":
                        zone.zone_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        zone.bottom_mm
                        - placement_footprint.bottom
                    ),
                },
            ),
        ]

    else:

        repair_options = []

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
        repair_options=repair_options,
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

    repair_options = []

    # --------------------------------------------------------
    # Move right if footprint crosses left boundary.
    # --------------------------------------------------------

    if footprint.left < min_x:

        repair_options.append(
            RepairOption(
                action="move",
                description=(
                    "Move the placement right "
                    "inside the room boundary."
                ),
                score=0.95,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "dx_mm": int(
                        min_x - footprint.left
                    ),
                    "dy_mm": 0,
                },
            )
        )

    # --------------------------------------------------------
    # Move left if footprint crosses right boundary.
    # --------------------------------------------------------

    if footprint.right > max_x:

        repair_options.append(
            RepairOption(
                action="move",
                description=(
                    "Move the placement left "
                    "inside the room boundary."
                ),
                score=0.94,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "dx_mm": int(
                        max_x - footprint.right
                    ),
                    "dy_mm": 0,
                },
            )
        )

    # --------------------------------------------------------
    # Move up if footprint crosses bottom boundary.
    # --------------------------------------------------------

    if footprint.bottom < min_y:

        repair_options.append(
            RepairOption(
                action="move",
                description=(
                    "Move the placement up "
                    "inside the room boundary."
                ),
                score=0.93,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        min_y - footprint.bottom
                    ),
                },
            )
        )

    # --------------------------------------------------------
    # Move down if footprint crosses top boundary.
    # --------------------------------------------------------

    if footprint.top > max_y:

        repair_options.append(
            RepairOption(
                action="move",
                description=(
                    "Move the placement down "
                    "inside the room boundary."
                ),
                score=0.92,
                parameters={
                    "placement_id":
                        placement.placement_id,
                    "dx_mm": 0,
                    "dy_mm": int(
                        max_y - footprint.top
                    ),
                },
            )
        )

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
        repair_options=repair_options,
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

        # The 900 mm occupied-desk clearance
        # is checked against task chairs only.
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

        # --------------------------------------------------------
        # Determine the clearance deficit.
        # --------------------------------------------------------

        deficit = int(
            DESK_REAR_CLEARANCE_MM
            - clearance
        )

        horizontal_gap = max(
            second_rect.left - first_rect.right,
            first_rect.left - second_rect.right,
            0,
        )

        vertical_gap = max(
            second_rect.bottom - first_rect.top,
            first_rect.bottom - second_rect.top,
            0,
        )

        # Deterministic vectors for BOTH possible repair targets.
        desk_dx = 0
        desk_dy = 0
        chair_dx = 0
        chair_dy = 0

        # --------------------------------------------------------
        # Horizontal separation.
        # --------------------------------------------------------

        if (
            horizontal_gap > 0
            and (
                vertical_gap == 0
                or horizontal_gap <= vertical_gap
            )
        ):

            # Chair is to the right of the desk.
            if (
                second_rect.left
                > first_rect.right
            ):
                desk_dx = -deficit
                chair_dx = deficit

            # Chair is to the left of the desk.
            else:
                desk_dx = deficit
                chair_dx = -deficit

        # --------------------------------------------------------
        # Vertical separation.
        # --------------------------------------------------------

        elif vertical_gap > 0:

            # Chair is below the desk.
            if (
                second_rect.bottom
                > first_rect.top
            ):
                desk_dy = -deficit
                chair_dy = deficit

            # Chair is above the desk.
            else:
                desk_dy = deficit
                chair_dy = -deficit

        # --------------------------------------------------------
        # Deterministic fallback.
        # --------------------------------------------------------

        else:
            desk_dy = -deficit
            chair_dy = deficit

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
                # ------------------------------------------------
                # OPTION 1: MOVE DESK
                # ------------------------------------------------
                RepairOption(
                    action="move",
                    description=(
                        "Move the desk away from "
                        "the paired chair to provide "
                        "900 mm rear clearance."
                    ),
                    score=0.85,
                    parameters={
                        "placement_id":
                            placement.placement_id,
                        "dx_mm":
                            desk_dx,
                        "dy_mm":
                            desk_dy,
                        "required_clearance_mm":
                            DESK_REAR_CLEARANCE_MM,
                    },
                ),

                # ------------------------------------------------
                # OPTION 2: MOVE CHAIR
                # ------------------------------------------------
                RepairOption(
                    action="move",
                    description=(
                        "Move the paired chair away "
                        "from the desk to provide "
                        "900 mm rear clearance."
                    ),
                    score=0.84,
                    parameters={
                        "placement_id":
                            other.placement_id,
                        "dx_mm":
                            chair_dx,
                        "dy_mm":
                            chair_dy,
                        "required_clearance_mm":
                            DESK_REAR_CLEARANCE_MM,
                    },
                ),
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

        # --------------------------------------------------------
        # Determine the clearance deficit.
        #
        # The repair moves the chair farther away from
        # the paired desk along the axis that currently
        # determines the measured clearance.
        #
        # If both axes have positive separation, the
        # smaller gap is the controlling axis, matching
        # _axis_clearance().
        # --------------------------------------------------------

        deficit = int(
            CHAIR_PULL_OUT_MM
            - clearance
        )

        horizontal_gap = max(
            desk_rect.left - chair_rect.right,
            chair_rect.left - desk_rect.right,
            0,
        )

        vertical_gap = max(
            desk_rect.bottom - chair_rect.top,
            chair_rect.bottom - desk_rect.top,
            0,
        )

        chair_dx = 0
        chair_dy = 0

        # --------------------------------------------------------
        # Horizontal clearance is the controlling axis.
        # --------------------------------------------------------

        if (
            horizontal_gap > 0
            and (
                vertical_gap == 0
                or horizontal_gap <= vertical_gap
            )
        ):

            # Chair is to the right of the desk.
            if (
                chair_rect.left
                > desk_rect.right
            ):
                chair_dx = deficit

            # Chair is to the left of the desk.
            else:
                chair_dx = -deficit

        # --------------------------------------------------------
        # Vertical clearance is the controlling axis.
        # --------------------------------------------------------

        elif vertical_gap > 0:

            # Chair is below the desk.
            if (
                chair_rect.bottom
                > desk_rect.top
            ):
                chair_dy = deficit

            # Chair is above the desk.
            else:
                chair_dy = -deficit

        # --------------------------------------------------------
        # Deterministic fallback.
        #
        # This branch should only occur for a non-overlapping
        # pair where the measured clearance is below the
        # requirement but neither axis has positive separation.
        # Overlap itself is handled by RB-GEO-006.
        # --------------------------------------------------------

        else:

            chair_dy = deficit

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
                        "Move the chair away from "
                        "the paired desk to provide "
                        "a 750 mm pull-out zone."
                    ),
                    score=0.85,
                    parameters={
                        "placement_id":
                            placement.placement_id,
                        "dx_mm":
                            chair_dx,
                        "dy_mm":
                            chair_dy,
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