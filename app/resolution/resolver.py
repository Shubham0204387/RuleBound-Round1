from app.requirements import RequirementSet

from app.resolution.models import (
    ResolutionEvidence,
    ResolvedFurnitureRequirement,
    ResolvedRequirementSet,
)


def infer_quantity(
    family: str,
    capacity,
    attributes,
):
    if capacity is None:
        return None, None, None

    if family == "chair":

        if "seating" in attributes:
            return (
                capacity,
                "high",
                "The brief explicitly requests seating for "
                "the room occupants, so room capacity is "
                "used as the required seating quantity.",
            )

        if "ergonomic" in attributes:
            return (
                capacity,
                "high",
                "Ergonomic chairs are explicitly requested "
                "for a room with a defined occupant capacity; "
                "one chair per occupant is inferred.",
            )

        if "task" in attributes:
            return (
                capacity,
                "medium",
                "Task seating quantity was not explicitly "
                "specified, so room capacity was used as a "
                "default seating requirement.",
            )

    if family == "desk" and "paired" in attributes:
        quantity = (capacity + 1) // 2

        return (
            quantity,
            "high",
            "Paired desks are assumed to support "
            "two occupants per desk.",
        )

    if family == "desk" and "individual" in attributes:
        return (
            capacity,
            "high",
            "Individual desks are assumed to provide "
            "one work position per occupant.",
        )

    return None, None, None


def resolve_furniture(
    requirements: RequirementSet,
):
    resolved = []

    for item in requirements.furniture:

        quantity = item.quantity
        status = "explicit"
        evidence = []

        if quantity is not None:

            evidence.append(
                ResolutionEvidence(
                    source="customer_brief",
                    reason=(
                        f"Quantity {quantity} was explicitly "
                        f"specified for {item.family}."
                    ),
                )
            )

        else:

            (
                inferred_quantity,
                confidence,
                reason,
            ) = infer_quantity(
                family=item.family,
                capacity=requirements.capacity,
                attributes=item.attributes,
            )

            if inferred_quantity is not None:

                quantity = inferred_quantity

                if confidence == "high":
                    status = "inferred_high"
                elif confidence == "medium":
                    status = "inferred_medium"

                evidence.append(
                    ResolutionEvidence(
                        source="resolution_engine",
                        reason=reason,
                    )
                )

            else:

                status = "unresolved"

                evidence.append(
                    ResolutionEvidence(
                        source="resolution_engine",
                        reason=(
                            "The brief does not provide "
                            "enough information to safely "
                            "infer a quantity."
                        ),
                    )
                )

        resolved.append(
            ResolvedFurnitureRequirement(
                family=item.family,
                quantity=quantity,
                attributes=list(item.attributes),
                movable=item.movable,
                fixed=item.fixed,
                quantity_status=status,
                evidence=evidence,
            )
        )

    return resolved


def resolve_requirements(
    requirements: RequirementSet,
) -> ResolvedRequirementSet:

    resolved_furniture = resolve_furniture(
        requirements
    )

    return ResolvedRequirementSet(
        room_id=requirements.room_id,
        capacity=requirements.capacity,
        furniture=resolved_furniture,
        spatial=list(requirements.spatial),
        preferences=list(requirements.preferences),
        priorities=list(requirements.priorities),
    )