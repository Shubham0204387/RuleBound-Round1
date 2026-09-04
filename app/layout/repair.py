"""
Deterministic layout repair engine.

The validator detects violations and proposes structured RepairOptions.
This module executes only repairs that produce a strictly decreasing
deterministic violation measure.

The repair engine does not weaken validation rules and does not invent
new furniture. If no strictly improving repair is available, the layout
is escalated.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.layout.models import Layout, Placement, RepairOption, Violation
from app.layout.placement import get_product_footprint


# ============================================================================
# CONSTANTS
# ============================================================================

MAX_REPAIR_STEPS = 12

# Requirement violations are intentionally expensive because they represent
# unresolved information that cannot safely be repaired geometrically.
REQUIREMENT_VIOLATION_WEIGHT = 1000000

# Unknown violations receive a deterministic fallback weight.
UNKNOWN_VIOLATION_WEIGHT = 100000


# ============================================================================
# RESULT MODELS
# ============================================================================

@dataclass
class RepairResult:
    """Result of one repair attempt."""

    applied: bool
    placement_id: Optional[str] = None
    action: Optional[str] = None
    previous_measure: int = 0
    resulting_measure: int = 0
    reason: str = ""


@dataclass
class Escalation:
    """Structured escalation when no improving repair exists."""

    escalation_id: str
    room_id: str
    reason: str
    violation_ids: List[str]
    termination_measure: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "room_id": self.room_id,
            "reason": self.reason,
            "violation_ids": list(self.violation_ids),
            "termination_measure": self.termination_measure,
        }


# ============================================================================
# TERMINATION MEASURE
# ============================================================================

def _violation_measure_value(
    violation: Violation,
) -> int:
    """
    Convert one violation into a deterministic non-negative measure.

    The measure represents the remaining amount of constraint failure.

    Examples:

        overlap_mm2 = 50000
            -> contribution = 50000

        required clearance = 900
        measured clearance = 600
            -> contribution = 300

        required wall offset = 100
        measured wall offset = 40
            -> contribution = 60

    Requirement violations receive a large fixed value because the system
    cannot safely infer the missing requirement.
    """

    rule_id = violation.rule_id

    # ------------------------------------------------------------------
    # Requirement violation
    # ------------------------------------------------------------------

    if rule_id == "RB-REQ-001":
        return REQUIREMENT_VIOLATION_WEIGHT

    # ------------------------------------------------------------------
    # Overlap
    # ------------------------------------------------------------------

    if rule_id == "RB-GEO-006":
        overlap = violation.measured.get(
            "overlap_mm2",
            0,
        )

        if isinstance(overlap, (int, float)):
            return max(0, int(overlap))

        return UNKNOWN_VIOLATION_WEIGHT

    # ------------------------------------------------------------------
    # Clearance violations
    # ------------------------------------------------------------------

    if rule_id in {
        "RB-GEO-004",
        "RB-GEO-008",
    }:
        measured = violation.measured.get(
            "clearance_mm",
            0,
        )

        required = violation.required.get(
            "clearance_mm",
            0,
        )

        if isinstance(measured, (int, float)) and isinstance(
            required,
            (int, float),
        ):
            return max(
                0,
                int(required - measured),
            )

        return UNKNOWN_VIOLATION_WEIGHT

    # ------------------------------------------------------------------
    # Wall offset
    # ------------------------------------------------------------------

    if rule_id == "RB-GEO-005":
        measured = violation.measured.get(
            "wall_offset_mm",
            0,
        )

        required = violation.required.get(
            "wall_offset_mm",
            0,
        )

        if isinstance(measured, (int, float)) and isinstance(
            required,
            (int, float),
        ):
            return max(
                0,
                int(required - measured),
            )

        return UNKNOWN_VIOLATION_WEIGHT

    # ------------------------------------------------------------------
    # Inside-room violation
    # ------------------------------------------------------------------

    if rule_id == "RB-GEO-007":
        # The validator currently exposes a boolean rather than a geometric
        # distance. Use a deterministic fixed penalty for this rule.
        inside_room = violation.measured.get(
            "inside_room"
        )

        if inside_room is False:
            return 1000

        return 0

    # ------------------------------------------------------------------
    # Generic geometry violation
    # ------------------------------------------------------------------

    if rule_id.startswith("RB-GEO-"):
        return 1000

    return UNKNOWN_VIOLATION_WEIGHT


def violation_measure(
    layout: Layout,
) -> int:
    """
    Calculate the deterministic termination measure.

    Important invariant:

        An accepted repair must satisfy:

            M(after) < M(before)

    M is always a non-negative integer.

    Therefore every accepted repair strictly decreases a well-founded
    measure and the repair process cannot continue indefinitely.
    """

    return sum(
        _violation_measure_value(violation)
        for violation in layout.violations
    )


# ============================================================================
# PLACEMENT HELPERS
# ============================================================================

def _find_placement(
    layout: Layout,
    placement_id: str,
) -> Optional[Placement]:
    """Find a placement by ID."""

    for placement in layout.placements:
        if placement.placement_id == placement_id:
            return placement

    return None


def _snapshot_placement(
    placement: Placement,
) -> Tuple[int, int, int]:
    """Capture mutable placement state."""

    return (
        placement.x_mm,
        placement.y_mm,
        placement.rotation_deg,
    )


def _restore_placement(
    placement: Placement,
    snapshot: Tuple[int, int, int],
) -> None:
    """Restore a placement to its previous state."""

    placement.x_mm = snapshot[0]
    placement.y_mm = snapshot[1]
    placement.rotation_deg = snapshot[2]


# ============================================================================
# REPAIR OPTION HANDLING
# ============================================================================

def _apply_move_from_wall(
    placement: Placement,
    option: RepairOption,
    room: Any,
    catalog: Any,
) -> bool:
    """
    Move a placement inward by the exact amount required to satisfy
    the minimum wall offset.

    Deterministic wall priority:

        left -> right -> bottom -> top
    """

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

    minimum_offset_mm = option.parameters.get(
        "minimum_offset_mm",
        100,
    )

    if not isinstance(
        minimum_offset_mm,
        (int, float),
    ):
        return False

    violations = [
        (
            "left",
            minimum_offset_mm
            - (footprint.left - room_min_x),
            (1, 0),
        ),
        (
            "right",
            minimum_offset_mm
            - (room_max_x - footprint.right),
            (-1, 0),
        ),
        (
            "bottom",
            minimum_offset_mm
            - (footprint.bottom - room_min_y),
            (0, 1),
        ),
        (
            "top",
            minimum_offset_mm
            - (room_max_y - footprint.top),
            (0, -1),
        ),
    ]

    for _, required_move, direction in violations:
        if required_move > 0:
            dx_mm = int(required_move * direction[0])
            dy_mm = int(required_move * direction[1])

            placement.x_mm += dx_mm
            placement.y_mm += dy_mm

            return True

    return False


def _apply_move(
    placement: Placement,
    option: RepairOption,
) -> bool:
    """
    Apply an explicitly parameterized movement.

    A move is executable only when numeric dx_mm and dy_mm values
    are supplied by the validator.
    """

    parameters = option.parameters

    dx_mm = parameters.get("dx_mm")
    dy_mm = parameters.get("dy_mm")

    if dx_mm is None or dy_mm is None:
        return False

    if not isinstance(dx_mm, (int, float)):
        return False

    if not isinstance(dy_mm, (int, float)):
        return False

    placement.x_mm += int(dx_mm)
    placement.y_mm += int(dy_mm)

    return True


def apply_repair_option(
    layout: Layout,
    violation: Violation,
    option: RepairOption,
    room: Any,
    catalog: Any,
) -> RepairResult:
    """
    Apply one validator-proposed repair.

    The caller is responsible for revalidation and deciding whether the
    resulting measure strictly decreased.
    """

    previous_measure = violation_measure(
        layout
    )

    placement_id = option.parameters.get(
        "placement_id"
    )

    if not placement_id:
        return RepairResult(
            applied=False,
            action=option.action,
            previous_measure=previous_measure,
            resulting_measure=previous_measure,
            reason=(
                "Repair option does not specify "
                "a placement_id."
            ),
        )

    placement = _find_placement(
        layout,
        placement_id,
    )

    if placement is None:
        return RepairResult(
            applied=False,
            placement_id=placement_id,
            action=option.action,
            previous_measure=previous_measure,
            resulting_measure=previous_measure,
            reason=(
                f"Placement '{placement_id}' "
                "was not found."
            ),
        )

    # ------------------------------------------------------------------
    # Wall-offset repair
    # ------------------------------------------------------------------

    if option.action == "move_from_wall":

        if not _apply_move_from_wall(
            placement,
            option,
            room,
            catalog,
        ):
            return RepairResult(
                applied=False,
                placement_id=placement_id,
                action=option.action,
                previous_measure=previous_measure,
                resulting_measure=previous_measure,
                reason=(
                    "Wall-offset repair could not determine "
                    "a deterministic inward movement."
                ),
            )

    # ------------------------------------------------------------------
    # Explicit movement repair
    # ------------------------------------------------------------------

    elif option.action == "move":

        if not _apply_move(
            placement,
            option,
        ):
            return RepairResult(
                applied=False,
                placement_id=placement_id,
                action=option.action,
                previous_measure=previous_measure,
                resulting_measure=previous_measure,
                reason=(
                    "Move repair requires numeric "
                    "dx_mm and dy_mm parameters."
                ),
            )

    # ------------------------------------------------------------------
    # Unsupported repair action
    # ------------------------------------------------------------------

    else:

        return RepairResult(
            applied=False,
            placement_id=placement_id,
            action=option.action,
            previous_measure=previous_measure,
            resulting_measure=previous_measure,
            reason=(
                f"Repair action '{option.action}' "
                "is not executable by the deterministic "
                "repair engine."
            ),
        )

    return RepairResult(
        applied=True,
        placement_id=placement_id,
        action=option.action,
        previous_measure=previous_measure,
        resulting_measure=previous_measure,
        reason=(
            "Candidate repair applied "
            "pending validation."
        ),
    )


# ============================================================================
# DETERMINISTIC REPAIR ORDER
# ============================================================================

def _repair_option_sort_key(
    violation: Violation,
    option: RepairOption,
) -> Tuple:
    """
    Produce a stable ordering for repair options.

    Higher score wins. All remaining fields provide deterministic
    tie-breaking.
    """

    score = (
        option.score
        if option.score is not None
        else 0.0
    )

    placement_id = str(
        option.parameters.get(
            "placement_id",
            "",
        )
    )

    dx_mm = option.parameters.get(
        "dx_mm",
        0,
    )

    dy_mm = option.parameters.get(
        "dy_mm",
        0,
    )

    return (
        -score,
        violation.violation_id,
        option.action,
        placement_id,
        dx_mm,
        dy_mm,
        option.description,
    )


def _ordered_repairs(
    layout: Layout,
) -> List[Tuple[Violation, RepairOption]]:
    """Return all repair options in deterministic order."""

    repairs = []

    for violation in layout.violations:
        for option in violation.repair_options:
            repairs.append(
                (
                    violation,
                    option,
                )
            )

    repairs.sort(
        key=lambda item: _repair_option_sort_key(
            item[0],
            item[1],
        )
    )

    return repairs


# ============================================================================
# BOUNDED REPAIR LOOP
# ============================================================================

def repair_layout(
    layout: Layout,
    validate,
    room: Any,
    catalog: Any,
    max_steps: int = MAX_REPAIR_STEPS,
) -> Tuple[Layout, Optional[Escalation]]:
    """
    Execute the deterministic repair loop.

    Pipeline:

        validate
            ↓
        measure
            ↓
        choose repair
            ↓
        apply
            ↓
        validate
            ↓
        strictly lower measure?
          ↙       ↘
        yes       no
         ↓         ↓
       accept    rollback
         ↓
      repeat

    A layout is escalated when no candidate repair strictly decreases
    the measure.

    The max_steps value is only a defensive upper bound. The primary
    termination argument is the strictly decreasing non-negative integer
    measure.
    """

    if max_steps <= 0:
        max_steps = MAX_REPAIR_STEPS

    layout = validate(
        layout,
        room,
        catalog,
    )

    for step in range(max_steps):

        # ------------------------------------------------------------
        # Success
        # ------------------------------------------------------------

        if not layout.violations:
            layout.status = "valid"

            return layout, None

        current_measure = violation_measure(
            layout
        )

        repairs = _ordered_repairs(
            layout
        )

        # ------------------------------------------------------------
        # No repair options
        # ------------------------------------------------------------

        if not repairs:

            violation_ids = [
                violation.violation_id
                for violation in layout.violations
            ]

            escalation = Escalation(
                escalation_id=(
                    f"E-{layout.room_id}-"
                    f"{step + 1:02d}"
                ),
                room_id=layout.room_id,
                reason=(
                    "No structured repair option is "
                    "available for the remaining "
                    "violations."
                ),
                violation_ids=violation_ids,
                termination_measure=current_measure,
            )

            layout.status = "unsatisfiable"

            return layout, escalation

        # ------------------------------------------------------------
        # Try candidate repairs
        # ------------------------------------------------------------

        progress = False

        for violation, option in repairs:

            placement_id = option.parameters.get(
                "placement_id"
            )

            if not placement_id:
                continue

            placement = _find_placement(
                layout,
                placement_id,
            )

            if placement is None:
                continue

            snapshot = _snapshot_placement(
                placement
            )

            attempt = apply_repair_option(
                layout,
                violation,
                option,
                room,
                catalog,
            )

            if not attempt.applied:
                continue

            # --------------------------------------------------------
            # Revalidate candidate
            # --------------------------------------------------------

            validated = validate(
                layout,
                room,
                catalog,
            )

            new_measure = violation_measure(
                validated
            )

            # --------------------------------------------------------
            # Strictly decreasing measure = ACCEPT
            # --------------------------------------------------------

            if new_measure < current_measure:

                layout = validated
                progress = True


                if new_measure == 0 or not layout.violations:
                    layout.status = "valid"
                    return layout, None

                break

            # --------------------------------------------------------
            # Otherwise rollback
            # --------------------------------------------------------

            _restore_placement(
                placement,
                snapshot,
            )

            layout = validate(
                layout,
                room,
                catalog,
            )

        # ------------------------------------------------------------
        # Continue after successful repair
        # ------------------------------------------------------------

        if progress:
            continue

        # ------------------------------------------------------------
        # No candidate reduced the measure
        # ------------------------------------------------------------

        violation_ids = [
            violation.violation_id
            for violation in layout.violations
        ]

        final_measure = violation_measure(
            layout
        )

        escalation = Escalation(
            escalation_id=(
                f"E-{layout.room_id}-"
                f"{step + 1:02d}"
            ),
            room_id=layout.room_id,
            reason=(
                "Available repair options were tested, "
                "but none strictly decreased the "
                "deterministic violation measure."
            ),
            violation_ids=violation_ids,
            termination_measure=final_measure,
        )

        layout.status = "unsatisfiable"

        return layout, escalation

    # =========================================================================
    # DEFENSIVE STEP LIMIT
    # =========================================================================

    final_measure = violation_measure(
        layout
    )

    escalation = Escalation(
        escalation_id=(
            f"E-{layout.room_id}-"
            f"{max_steps:02d}"
        ),
        room_id=layout.room_id,
        reason=(
            "Repair step limit reached before "
            "the layout became valid."
        ),
        violation_ids=[
            violation.violation_id
            for violation in layout.violations
        ],
        termination_measure=final_measure,
    )

    layout.status = "unsatisfiable"

    return layout, escalation