from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Evidence:
    """
    Records where a requirement came from.

    This supports explainability and decision tracing.
    """

    source: str
    text: str


@dataclass
class FurnitureRequirement:
    """
    Represents one type of furniture/accessory requested
    by the customer.
    """

    family: str
    quantity: Optional[int] = None
    attributes: List[str] = field(default_factory=list)
    movable: Optional[bool] = None
    fixed: Optional[bool] = None
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class SpatialRequirement:
    """
    Represents a spatial requirement extracted from the brief.
    """

    requirement_type: str
    value: Optional[str] = None
    priority: str = "normal"
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class Preference:
    """
    Represents something the customer prefers but which
    may not be a mandatory requirement.
    """

    category: str
    value: str
    strength: str = "preferred"
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class Priority:
    """
    Represents an explicit customer priority.

    Example:
        egress > maximum density
    """

    higher_priority: str
    lower_priority: str
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class RequirementIssue:
    """
    Represents an issue discovered while validating
    extracted requirements.
    """

    issue_type: str
    message: str
    severity: str = "warning"
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class RequirementValidation:
    """
    Result of validating a RequirementSet.
    """

    valid: bool
    issues: List[RequirementIssue] = field(
        default_factory=list
    )


@dataclass
class RequirementSet:
    """
    Complete structured interpretation of a customer brief.
    """

    room_id: str

    capacity: Optional[int] = None

    furniture: List[FurnitureRequirement] = field(
        default_factory=list
    )

    spatial: List[SpatialRequirement] = field(
        default_factory=list
    )

    preferences: List[Preference] = field(
        default_factory=list
    )

    priorities: List[Priority] = field(
        default_factory=list
    )

    evidence: List[Evidence] = field(
        default_factory=list
    )