from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ResolutionEvidence:
    """
    Explains why a resolved value was produced.
    """

    source: str
    reason: str


@dataclass
class ResolvedFurnitureRequirement:
    """
    Furniture requirement after resolving quantities
    and other necessary implications.
    """

    family: str
    quantity: Optional[int]

    attributes: List[str] = field(
        default_factory=list
    )

    movable: Optional[bool] = None
    fixed: Optional[bool] = None

    # Possible values:
    # explicit
    # inferred_high
    # inferred_medium
    # unresolved
    quantity_status: str = "explicit"

    evidence: List[ResolutionEvidence] = field(
        default_factory=list
    )


@dataclass
class ResolvedRequirementSet:
    """
    Fully resolved requirements used by downstream
    product-selection and layout systems.
    """

    room_id: str
    capacity: Optional[int]

    furniture: List[
        ResolvedFurnitureRequirement
    ] = field(default_factory=list)

    spatial: list = field(
        default_factory=list
    )

    preferences: list = field(
        default_factory=list
    )

    priorities: list = field(
        default_factory=list
    )

    resolution_notes: List[
        ResolutionEvidence
    ] = field(default_factory=list)