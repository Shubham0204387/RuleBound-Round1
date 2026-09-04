"""
Furniture Layout Assembly Module

This module handles the assembly of furniture layouts in rooms,
including workstation placement with desks and chairs, as well as
other furniture types like collaboration, storage, and accessory items.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from app.layout.models import Layout, Placement
from app.layout.candidates import (
    generate_candidates,
    find_chair_candidates_for_desk,
)
from app.layout.placement import (
    placement_overlaps,
    get_product_footprint,
)
from app.layout.zones import build_zones


# ============================================================================
# CONSTANTS
# ============================================================================

DESK_REAR_CLEARANCE_MM = 900
CHAIR_PULL_OUT_MM = 750


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AssemblyResult:
    """Result of a furniture assembly operation."""
    
    layout: Layout
    unresolved_families: List[str]


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _append_candidate(
    candidate: Any,
    placements: List[Placement],
    counter: int,
) -> Placement:
    """
    Append a candidate placement to the placements list.
    
    Args:
        candidate: Candidate object containing placement data
        placements: List of existing placements
        counter: Current placement counter for ID generation
        
    Returns:
        The created Placement object
    """
    source = candidate.placement

    placement = Placement(
        placement_id=f"P-{counter:04d}",
        sku=source.sku,
        finish_id=source.finish_id,
        x_mm=source.x_mm,
        y_mm=source.y_mm,
        rotation_deg=source.rotation_deg,
    )

    placements.append(placement)
    return placement


def _overlaps_any(
    placement: Placement,
    placements: List[Placement],
    catalog: Any,
) -> bool:
    """
    Check if a placement overlaps with any existing placement.
    
    Args:
        placement: Placement to check
        placements: List of existing placements
        catalog: Product catalog
        
    Returns:
        True if overlaps with any placement, False otherwise
    """
    for existing in placements:
        if placement_overlaps(placement, existing, catalog):
            return True
    return False


def _clearance_between(
    first: Placement,
    second: Placement,
    catalog: Any,
) -> float:
    """
    Calculate the minimum axis-aligned clearance between two furniture footprints.
    
    Args:
        first: First placement
        second: Second placement
        catalog: Product catalog
        
    Returns:
        Minimum clearance distance in millimeters
    """
    first_fp = get_product_footprint(first, catalog)
    second_fp = get_product_footprint(second, catalog)

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

    return min(horizontal, vertical)


def _desk_is_valid(
    desk: Placement,
    existing_desks: List[Placement],
    placements: List[Placement],
    catalog: Any,
) -> bool:
    """
    Validate a desk against already committed furniture.
    
    Desk-to-desk distance is NOT RB-GEO-004.
    Only physical overlap is rejected here.
    Desk/chair directional clearances are checked separately.
    
    Args:
        desk: Desk placement to validate
        existing_desks: List of existing desk placements
        placements: List of all existing placements
        catalog: Product catalog
        
    Returns:
        True if desk is valid, False otherwise
    """
    if _overlaps_any(desk, placements, catalog):
        return False
    return True


def _chair_is_valid_for_paired_desk(
    chair: Placement,
    desk: Placement,
    placements: List[Placement],
    catalog: Any,
) -> bool:
    """
    Validate a chair against its paired desk.
    
    The chair must:
    1. Not overlap existing furniture.
    2. Not overlap its paired desk.
    3. Have at least 750 mm clearance from its paired desk.
    
    Args:
        chair: Chair placement to validate
        desk: Paired desk placement
        placements: List of all existing placements
        catalog: Product catalog
        
    Returns:
        True if chair is valid, False otherwise
    """
    if _overlaps_any(chair, placements, catalog):
        return False

    if placement_overlaps(chair, desk, catalog):
        return False

    clearance = _clearance_between(chair, desk, catalog)
    return clearance >= CHAIR_PULL_OUT_MM


def _build_zones(room: Any) -> List[Any]:
    """
    Build a combined list of all zone types for a room.
    
    Args:
        room: Room object
        
    Returns:
        Combined list of all zone objects
    """
    zones = build_zones(room)
    return (
        zones.get("usable", [])
        + zones.get("perimeter", [])
        + zones.get("open", [])
        + zones.get("windows", [])
        + zones.get("doors", [])
        + zones.get("egress", [])
        + zones.get("walkway", [])
    )


# ============================================================================
# WORKSTATION PLACEMENT
# ============================================================================

def _place_workstations(
    room: Any,
    desk_product: Any,
    chair_product: Any,
    desk_quantity: int,
    chair_quantity: int,
    finish_id: str,
    zones: List[Any],
    catalog: Any,
    placements: List[Placement],
    step_mm: int,
    candidates_per_item: int,
    placement_counter: int,
) -> Tuple[List[Placement], List[Placement], int]:
    """
    Constructive workstation placement.
    
    This deliberately avoids the previous global workstation compatibility search.
    Desk locations are selected first, then chairs are assigned locally to those desks.
    
    The algorithm is bounded and deterministic so that difficult rooms cannot
    cause an unbounded recursive search.
    
    Required workstation rules:
        - desk/chair must not overlap
        - chair requires CHAIR_PULL_OUT_MM clearance
        - chairs cannot overlap each other
        - chairs cannot overlap any selected desk
        - furniture already present in the room is respected
    
    Args:
        room: Room object
        desk_product: Product object for desks
        chair_product: Product object for chairs
        desk_quantity: Number of desks required
        chair_quantity: Number of chairs required
        finish_id: Finish ID for furniture
        zones: List of valid zones
        catalog: Product catalog
        placements: List of existing placements
        step_mm: Step size for candidate generation
        candidates_per_item: Max candidates per item
        placement_counter: Current placement counter
        
    Returns:
        Tuple of (desks, chairs, placement_counter)
    """
    desks = []
    chairs = []

    # Early exit if no workstations needed
    if desk_quantity <= 0 or chair_quantity <= 0:
        return desks, chairs, placement_counter

    # Calculate chairs per desk
    chairs_per_desk = chair_quantity // desk_quantity
    if chairs_per_desk <= 0:
        return desks, chairs, placement_counter

    extra_chairs = chair_quantity % desk_quantity

    # ------------------------------------------------------------------------
    # Generate desk candidates
    # ------------------------------------------------------------------------

    desk_candidates = generate_candidates(
        room=room,
        product=desk_product,
        family="desk",
        finish_id=finish_id,
        zones=zones,
        catalog=catalog,
        existing_placements=placements,
        step_mm=step_mm,
        max_candidates=300,
    )


    if not desk_candidates:
        return [], [], placement_counter

    # ------------------------------------------------------------------------
    # Convert candidates to temporary placements
    # ------------------------------------------------------------------------

    desk_entries = []
    seen_desks = set()

    for candidate in desk_candidates:
        source = candidate.placement
        key = (source.x_mm, source.y_mm, source.rotation_deg)

        if key in seen_desks:
            continue

        seen_desks.add(key)

        desk = Placement(
            placement_id="TEMP-DESK",
            sku=source.sku,
            finish_id=source.finish_id,
            x_mm=source.x_mm,
            y_mm=source.y_mm,
            rotation_deg=source.rotation_deg,
        )

        fp = get_product_footprint(desk, catalog)

        desk_entries.append({
            "desk": desk,
            "fp": fp,
            "score": candidate.strategy_score,
        })

    # ------------------------------------------------------------------------
    # Rank desks
    # ------------------------------------------------------------------------

    def desk_rank(entry: Dict[str, Any]) -> Tuple[float, float, float, int]:
        """Rank desks by score and position."""
        desk = entry["desk"]
        return (
            -entry["score"],
            desk.y_mm,
            desk.x_mm,
            desk.rotation_deg,
        )

    desk_entries.sort(key=desk_rank)

    # Limit search space
    MAX_DESKS_TO_SEARCH = min(len(desk_entries), 180)
    desk_entries = desk_entries[:MAX_DESKS_TO_SEARCH]

    # ------------------------------------------------------------------------
    # Existing furniture footprints
    # ------------------------------------------------------------------------

    existing_fps = []
    for existing in placements:
        existing_fps.append((existing, get_product_footprint(existing, catalog)))

    def overlaps_existing(fp: Any) -> bool:
        """Check if a footprint overlaps any existing furniture."""
        for _, existing_fp in existing_fps:
            if fp.overlaps(existing_fp):
                return True
        return False

    # ------------------------------------------------------------------------
    # Desk compatibility
    # ------------------------------------------------------------------------

    def desk_compatible(entry: Dict[str, Any], selected: List[Dict[str, Any]]) -> bool:
        """
        Check if a desk is compatible with selected desks.
        
        Desks need physical separation but do NOT require the chair clearance
        rule between each other.
        """
        fp = entry["fp"]

        if overlaps_existing(fp):
            return False

        for selected_entry in selected:
            if fp.overlaps(selected_entry["fp"]):
                return False

        return True

    # ------------------------------------------------------------------------
    # Chair generation cache
    # ------------------------------------------------------------------------

    chair_cache = {}

    def chair_candidates_for_desk(
        desk: Placement,
        selected_desks: List[Dict[str, Any]],
    ) -> List[Tuple[Placement, Any, float]]:
        """
        Get chair candidates for a desk considering selected desks.
        
        A chair must not physically overlap any selected desk. Only its
        associated desk has the pull-out clearance requirement.
        """
        key = (desk.x_mm, desk.y_mm, desk.rotation_deg)

        if key in chair_cache:
            raw_candidates = chair_cache[key]
        else:
            raw_candidates = find_chair_candidates_for_desk(
                room=room,
                desk=desk,
                chair_product=chair_product,
                finish_id=finish_id,
                zones=zones,
                catalog=catalog,
                existing_placements=(
                    placements + [item["desk"] for item in selected_desks]
                ),
                step_mm=step_mm,
                max_candidates=120,
            )
            chair_cache[key] = raw_candidates

        valid = []
        seen = set()
        desk_fp = get_product_footprint(desk, catalog)

        for candidate in raw_candidates:
            source = candidate.placement

            chair = Placement(
                placement_id="TEMP-CHAIR",
                sku=source.sku,
                finish_id=source.finish_id,
                x_mm=source.x_mm,
                y_mm=source.y_mm,
                rotation_deg=source.rotation_deg,
            )

            chair_key = (chair.x_mm, chair.y_mm, chair.rotation_deg)
            if chair_key in seen:
                continue

            seen.add(chair_key)
            chair_fp = get_product_footprint(chair, catalog)

            # Check against desk
            if chair_fp.overlaps(desk_fp):
                continue

            # Check against existing furniture
            if overlaps_existing(chair_fp):
                continue

            # Check clearance from desk
            clearance = _clearance_between(chair, desk, catalog)
            if clearance < CHAIR_PULL_OUT_MM:
                continue

            # Check against selected desks
            overlaps_selected_desk = False
            for selected_entry in selected_desks:
                if chair_fp.overlaps(selected_entry["fp"]):
                    overlaps_selected_desk = True
                    break

            if overlaps_selected_desk:
                continue

            valid.append((chair, chair_fp, candidate.strategy_score))

        valid.sort(key=lambda item: (-item[2], item[0].y_mm, item[0].x_mm, item[0].rotation_deg))
        return valid

    # ------------------------------------------------------------------------
    # Chair assignment
    # ------------------------------------------------------------------------

    MAX_CHAIRS_PER_DESK_SEARCH = 30

    def assign_chairs(selected_desks: List[Dict[str, Any]]) -> Optional[List[Tuple[Placement, Any, float]]]:
        """
        Assign chairs to selected desks.
        
        Returns:
            List of assigned chairs or None if assignment fails
        """
        chair_options = []

        for desk_index, desk_entry in enumerate(selected_desks):
            required = chairs_per_desk + (1 if desk_index < extra_chairs else 0)

            candidates = chair_candidates_for_desk(desk_entry["desk"], selected_desks)
            candidates = candidates[:MAX_CHAIRS_PER_DESK_SEARCH]

            if len(candidates) < required:
                return None

            chair_options.append((required, candidates))

        # Most constrained desk first
        order = sorted(
            range(len(chair_options)),
            key=lambda index: len(chair_options[index][1]),
        )

        selected_chairs = []

        # Bound the nested chair-assignment search so difficult rooms
        # terminate deterministically instead of exploring an unbounded
        # recursive search tree.
        chair_search_nodes = 0
        MAX_CHAIR_SEARCH_NODES = 12000

        def chair_search(position: int) -> Optional[List[Tuple[Placement, Any, float]]]:
            """Recursive chair assignment search with a deterministic node bound."""
            nonlocal chair_search_nodes

            chair_search_nodes += 1

            if chair_search_nodes > MAX_CHAIR_SEARCH_NODES:
                return None

            if position == len(order):
                return list(selected_chairs)

            desk_index = order[position]
            required, candidates = chair_options[desk_index]

            def choose_for_desk(
                candidate_index: int,
                chosen_for_desk: List[Tuple[Placement, Any, float]],
            ) -> Optional[List[Tuple[Placement, Any, float]]]:
                """Choose chairs for a specific desk."""
                nonlocal chair_search_nodes

                chair_search_nodes += 1

                if chair_search_nodes > MAX_CHAIR_SEARCH_NODES:
                    return None

                if len(chosen_for_desk) == required:
                    result = chair_search(position + 1)
                    if result is not None:
                        return result
                    return None

                remaining = required - len(chosen_for_desk)
                available = len(candidates) - candidate_index

                if available < remaining:
                    return None

                for index in range(candidate_index, len(candidates)):
                    chair_search_nodes += 1

                    if chair_search_nodes > MAX_CHAIR_SEARCH_NODES:
                        return None

                    chair, chair_fp, _ = candidates[index]

                    # Check conflicts with selected chairs
                    conflict = False
                    for existing_chair, existing_fp, _ in selected_chairs:
                        if chair_fp.overlaps(existing_fp):
                            conflict = True
                            break

                    if conflict:
                        continue

                    for existing_chair, existing_fp, _ in chosen_for_desk:
                        if chair_fp.overlaps(existing_fp):
                            conflict = True
                            break

                    if conflict:
                        continue

                    chosen_for_desk.append((chair, chair_fp, 0))
                    selected_chairs.append((chair, chair_fp, 0))

                    result = choose_for_desk(index + 1, chosen_for_desk)
                    if result is not None:
                        return result

                    selected_chairs.pop()
                    chosen_for_desk.pop()

                return None

            return choose_for_desk(0, [])

        return chair_search(0)

    # ------------------------------------------------------------------------
    # Desk search
    # ------------------------------------------------------------------------

    search_nodes = 0
    MAX_DESK_SEARCH_NODES = 12000
    solution = None

    def search_desks(
        start_index: int,
        selected: List[Dict[str, Any]],
    ) -> Optional[Tuple[List[Dict[str, Any]], List[Tuple[Placement, Any, float]]]]:
        """
        Recursive desk search with chair feasibility pruning.
        
        Key optimization: choose desk locations and immediately test chair
        feasibility. Never build a global workstation graph.
        """
        nonlocal search_nodes, solution

        search_nodes += 1

        if search_nodes > MAX_DESK_SEARCH_NODES:
            return None

        if len(selected) == desk_quantity:
            chairs_result = assign_chairs(selected)
            if chairs_result is not None:
                solution = (list(selected), chairs_result)
                return solution
            return None

        remaining = desk_quantity - len(selected)

        if len(desk_entries) - start_index < remaining:
            return None

        for index in range(start_index, len(desk_entries)):
            entry = desk_entries[index]

            if not desk_compatible(entry, selected):
                continue

            selected.append(entry)

            # Early chair feasibility check - important pruning step
            required = chairs_per_desk + (1 if (len(selected) - 1) < extra_chairs else 0)
            chair_probe = chair_candidates_for_desk(entry["desk"], selected)

            if len(chair_probe) >= required:
                result = search_desks(index + 1, selected)
                if result is not None:
                    return result

            selected.pop()

        return None

    # Execute search
    result = search_desks(0, [])

    if result is None:
        return [], [], placement_counter

    selected_desks, selected_chairs = result


    # Diagnostics
    for number, entry in enumerate(selected_desks, 1):
        desk = entry["desk"]


    # ------------------------------------------------------------------------
    # Commit desks
    # ------------------------------------------------------------------------

    counter = placement_counter

    for entry in selected_desks:
        source = entry["desk"]
        committed = Placement(
            placement_id=f"P-{counter:04d}",
            sku=source.sku,
            finish_id=source.finish_id,
            x_mm=source.x_mm,
            y_mm=source.y_mm,
            rotation_deg=source.rotation_deg,
        )
        counter += 1
        placements.append(committed)
        desks.append(committed)

    # ------------------------------------------------------------------------
    # Commit chairs
    # ------------------------------------------------------------------------

    for chair, _, _ in selected_chairs:
        committed = Placement(
            placement_id=f"P-{counter:04d}",
            sku=chair.sku,
            finish_id=chair.finish_id,
            x_mm=chair.x_mm,
            y_mm=chair.y_mm,
            rotation_deg=chair.rotation_deg,
        )
        counter += 1
        placements.append(committed)
        chairs.append(committed)

    return desks, chairs, counter


# ============================================================================
# MAIN ASSEMBLY FUNCTION
# ============================================================================

def assemble_layout(
    room: Any,
    selected_products: Dict[str, Any],
    requirements: Any,
    catalog: Any,
    finish_id: str = "F01",
    step_mm: int = 300,
    candidates_per_item: int = 100,
) -> AssemblyResult:
    """
    Assemble the room as complete workstations.
    
    Primary strategy:
        1. desk + required chairs
        2. collaboration
        3. storage
        4. accessory
        5. other furniture
    
    Geometry is never weakened merely to satisfy quantity.
    
    Args:
        room: Room object
        selected_products: Dictionary mapping family to product
        requirements: Requirements object
        catalog: Product catalog
        finish_id: Finish ID for furniture
        step_mm: Step size for candidate generation
        candidates_per_item: Max candidates per item
        
    Returns:
        AssemblyResult containing layout and unresolved families
    """
    # Build zones
    zones = _build_zones(room)

    placements: List[Placement] = []
    unresolved_families: List[str] = []

    placement_counter = 1

    # ------------------------------------------------------------------------
    # Requirement lookup
    # ------------------------------------------------------------------------

    requirements_by_family = {
        requirement.family: requirement
        for requirement in requirements.furniture
    }

    desk_requirement = requirements_by_family.get("desk")
    chair_requirement = requirements_by_family.get("chair")

    desk_product = selected_products.get("desk")
    chair_product = selected_products.get("chair")

    # ------------------------------------------------------------------------
    # Requested quantities
    # ------------------------------------------------------------------------

    requested_desks = (
        desk_requirement.quantity
        if (desk_requirement is not None and desk_requirement.quantity is not None)
        else 0
    )

    requested_chairs = (
        chair_requirement.quantity
        if (chair_requirement is not None and chair_requirement.quantity is not None)
        else 0
    )

    # ------------------------------------------------------------------------
    # Workstation assembly
    # ------------------------------------------------------------------------

    desks = []
    chairs = []

    workstations_attempted = (
        requested_desks > 0
        and requested_chairs > 0
        and desk_product is not None
        and chair_product is not None
    )

    if workstations_attempted:
        desks, chairs, placement_counter = _place_workstations(
            room=room,
            desk_product=desk_product,
            chair_product=chair_product,
            desk_quantity=requested_desks,
            chair_quantity=requested_chairs,
            finish_id=finish_id,
            zones=zones,
            catalog=catalog,
            placements=placements,
            step_mm=step_mm,
            candidates_per_item=candidates_per_item,
            placement_counter=placement_counter,
        )

    # ------------------------------------------------------------------------
    # Workstation quantity reporting
    # ------------------------------------------------------------------------

    if workstations_attempted:
        if len(desks) < requested_desks:
            unresolved_families.append("desk")

        if len(chairs) < requested_chairs:
            unresolved_families.append("chair")
    elif requested_desks > 0:
        unresolved_families.append("desk")

    # ------------------------------------------------------------------------
    # Remaining furniture
    # ------------------------------------------------------------------------

    remaining_requirements = [
        requirement
        for requirement in requirements.furniture
        if requirement.family != "desk"
        and not (requirement.family == "chair" and workstations_attempted)
    ]

    family_priority = {
        "collaboration": 1,
        "storage": 2,
        "accessory": 3,
    }

    remaining_requirements.sort(
        key=lambda requirement: (
            family_priority.get(requirement.family, 99),
            requirement.family,
        )
    )

    # ------------------------------------------------------------------------
    # Place remaining furniture
    # ------------------------------------------------------------------------

    for requirement in remaining_requirements:
        family = requirement.family

        if requirement.quantity is None:
            unresolved_families.append(family)
            continue

        product = selected_products.get(family)

        if product is None:
            unresolved_families.append(family)
            continue

        placed_count = 0

        for _ in range(requirement.quantity):
            candidates = generate_candidates(
                room=room,
                product=product,
                family=family,
                finish_id=finish_id,
                zones=zones,
                catalog=catalog,
                existing_placements=placements,
                step_mm=step_mm,
                max_candidates=max(candidates_per_item, 100),
            )

            accepted = None

            for candidate in candidates:
                if _overlaps_any(candidate.placement, placements, catalog):
                    continue
                accepted = candidate
                break

            if accepted is None:
                break

            _append_candidate(accepted, placements, placement_counter)
            placement_counter += 1
            placed_count += 1

        if placed_count < requirement.quantity:
            unresolved_families.append(family)

    # ------------------------------------------------------------------------
    # Remove duplicates
    # ------------------------------------------------------------------------

    unresolved_families = list(dict.fromkeys(unresolved_families))

    # ------------------------------------------------------------------------
    # Assembly status
    # ------------------------------------------------------------------------

    status = "valid" if not unresolved_families else "invalid"

    layout = Layout(
        room_id=room.room_id,
        placements=placements,
        violations=[],
        status=status,
    )

    return AssemblyResult(
        layout=layout,
        unresolved_families=unresolved_families,
    )