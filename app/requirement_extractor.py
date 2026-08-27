import re
from typing import List, Optional

from app.requirements import (
    Evidence,
    FurnitureRequirement,
    Preference,
    Priority,
    RequirementSet,
    SpatialRequirement,
)


NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def number_from_text(value: str) -> Optional[int]:
    """Convert a numeric or written number into an integer."""

    value = value.lower().strip()

    if value.isdigit():
        return int(value)

    return NUMBER_WORDS.get(value)


def add_furniture(
    requirements: RequirementSet,
    family: str,
    quantity: Optional[int],
    attributes: Optional[List[str]],
    evidence_text: str,
    movable: Optional[bool] = None,
    fixed: Optional[bool] = None,
):
    """Add a furniture requirement with evidence."""

    requirements.furniture.append(
        FurnitureRequirement(
            family=family,
            quantity=quantity,
            attributes=attributes or [],
            movable=movable,
            fixed=fixed,
            evidence=[
                Evidence(
                    source="customer_brief",
                    text=evidence_text,
                )
            ],
        )
    )


def extract_capacity(text: str) -> Optional[int]:
    """
    Extract phrases such as:

        12-person
        16 person
        team of 10
        for 14 people
    """

    patterns = [
        r"(\d+)\s*[- ]?person",
        r"team\s+of\s+(\d+)",
        r"for\s+(\d+)\s+people",
        r"(\d+)\s+people",
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())

        if match:
            return int(match.group(1))

    return None


def extract_furniture_requirements(
    text: str,
    requirements: RequirementSet,
):
    """Extract common furniture requirements."""

    lower = text.lower()

    # Paired desks
    if "paired desk" in lower or "paired desks" in lower:
        add_furniture(
            requirements,
            family="desk",
            quantity=None,
            attributes=["paired"],
            evidence_text="paired desks",
        )

    # Fixed work positions
    match = re.search(
        r"(\d+)\s+fixed\s+work\s+positions?",
        lower,
    )

    if match:
        add_furniture(
            requirements,
            family="desk",
            quantity=int(match.group(1)),
            attributes=["work_position"],
            fixed=True,
            evidence_text=match.group(0),
        )

    # Desk positions
    match = re.search(
        r"(\d+)\s+desk\s+positions?",
        lower,
    )

    if match:
        add_furniture(
            requirements,
            family="desk",
            quantity=int(match.group(1)),
            attributes=["work_position"],
            evidence_text=match.group(0),
        )

    # Individual desks
    if "individual desks" in lower:
        add_furniture(
            requirements,
            family="desk",
            quantity=None,
            attributes=["individual"],
            evidence_text="individual desks",
        )

    # Ergonomic chairs
    if "ergonomic chair" in lower or "ergonomic chairs" in lower:
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["ergonomic"],
            evidence_text="ergonomic chairs",
        )

    # Task seating
    if "task seating" in lower:
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["task"],
            evidence_text="task seating",
        )

    # Seating for X
    match = re.search(
        r"seating\s+for\s+(\d+)",
        lower,
    )

    if match:
        add_furniture(
            requirements,
            family="chair",
            quantity=int(match.group(1)),
            attributes=["seating"],
            evidence_text=match.group(0),
        )

    # Lockable storage
    match = re.search(
        r"(\d+|one|two|three|four|five)\s+lockable\s+storage\s+units?",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="storage",
            quantity=quantity,
            attributes=["lockable"],
            evidence_text=match.group(0),
        )

    # Accessible storage
    if "accessible storage" in lower:
        add_furniture(
            requirements,
            family="storage",
            quantity=None,
            attributes=["accessible"],
            evidence_text="accessible storage",
        )

    # Distributed storage
    if "distributed storage" in lower:
        add_furniture(
            requirements,
            family="storage",
            quantity=None,
            attributes=["distributed"],
            evidence_text="distributed storage",
        )

    # Generic storage
    if (
        "storage" in lower
        and not any(
            item.family == "storage"
            for item in requirements.furniture
        )
    ):
        add_furniture(
            requirements,
            family="storage",
            quantity=None,
            attributes=[],
            evidence_text="storage",
        )

    # Collaboration tables
    match = re.search(
        r"(\d+|one|two|three|four|five)\s+"
        r"(?:compact\s+)?collaboration\s+tables?",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        attributes = ["collaboration"]

        if "compact" in match.group(0):
            attributes.append("compact")

        add_furniture(
            requirements,
            family="collaboration",
            quantity=quantity,
            attributes=attributes,
            evidence_text=match.group(0),
        )

    # Generic collaboration zones
    match = re.search(
        r"(\d+|one|two|three|four|five)\s+"
        r"collaboration\s+zones?",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="collaboration",
            quantity=quantity,
            attributes=["zone"],
            evidence_text=match.group(0),
        )

    # Touchdown table
    match = re.search(
        r"(\d+|one|two|three|four|five)"
        r"(?:-|\s+)person\s+touchdown\s+table",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="collaboration",
            quantity=1,
            attributes=[
                "touchdown",
                f"capacity_{quantity}",
            ],
            evidence_text=match.group(0),
        )

    # Acoustic accessories
    if "acoustic accessories" in lower:
        add_furniture(
            requirements,
            family="accessory",
            quantity=None,
            attributes=["acoustic", "compatible_only"],
            evidence_text="acoustic accessories",
        )

    # Writable accessories
    if "writable accessories" in lower:
        add_furniture(
            requirements,
            family="accessory",
            quantity=None,
            attributes=["writable"],
            evidence_text="writable accessories",
        )


def extract_spatial_requirements(
    text: str,
    requirements: RequirementSet,
):
    """Extract spatial requirements and constraints."""

    lower = text.lower()

    spatial_patterns = [
        (
            "clear_route",
            ["clear route", "clear circulation"],
        ),
        (
            "generous_egress",
            ["generous egress", "egress path"],
        ),
        (
            "accessible_circulation",
            ["accessible circulation"],
        ),
        (
            "preserve_daylight",
            ["preserve daylight"],
        ),
        (
            "protect_windows",
            ["windows must not be obstructed",
             "window must not be obstructed",
             "do not obstruct windows"],
        ),
        (
            "protect_doors",
            ["both doors must remain usable",
             "door must remain usable"],
        ),
        (
            "protect_egress",
            ["do not narrow the marked egress route",
             "prioritise the egress route"],
        ),
    ]

    for requirement_type, phrases in spatial_patterns:
        for phrase in phrases:
            if phrase in lower:
                priority = "normal"

                if requirement_type in {
                    "protect_egress",
                    "protect_doors",
                }:
                    priority = "high"

                requirements.spatial.append(
                    SpatialRequirement(
                        requirement_type=requirement_type,
                        priority=priority,
                        evidence=[
                            Evidence(
                                source="customer_brief",
                                text=phrase,
                            )
                        ],
                    )
                )
                break


def extract_preferences(
    text: str,
    requirements: RequirementSet,
):
    """Extract customer preferences."""

    lower = text.lower()

    if "natural oak" in lower:
        requirements.preferences.append(
            Preference(
                category="finish",
                value="natural_oak",
                strength="preferred",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="natural oak",
                    )
                ],
            )
        )

    if "graphite" in lower:
        requirements.preferences.append(
            Preference(
                category="finish",
                value="graphite",
                strength="preferred",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="graphite",
                    )
                ],
            )
        )

    if "durable neutral finishes" in lower:
        requirements.preferences.append(
            Preference(
                category="finish",
                value="durable_neutral",
                strength="preferred",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="durable neutral finishes",
                    )
                ],
            )
        )

    if "visually open" in lower:
        requirements.preferences.append(
            Preference(
                category="layout",
                value="visually_open",
                strength="preferred",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="visually open",
                    )
                ],
            )
        )

    if "quiet focus" in lower or "focus library" in lower:
        requirements.preferences.append(
            Preference(
                category="environment",
                value="quiet_focus",
                strength="preferred",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="quiet focus",
                    )
                ],
            )
        )


def extract_priorities(
    text: str,
    requirements: RequirementSet,
):
    """Extract explicit customer priorities."""

    lower = text.lower()

    if "egress route" in lower and "maximum density" in lower:
        requirements.priorities.append(
            Priority(
                higher_priority="egress",
                lower_priority="maximum_density",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text=(
                            "Prioritise the egress route "
                            "over maximum density."
                        ),
                    )
                ],
            )
        )


def extract_requirements(
    room_id: str,
    brief_text: str,
) -> RequirementSet:
    """
    Convert a natural-language customer brief into
    a structured RequirementSet.
    """

    requirements = RequirementSet(
        room_id=room_id,
        capacity=extract_capacity(brief_text),
    )

    requirements.evidence.append(
        Evidence(
            source="customer_brief",
            text=brief_text,
        )
    )

    extract_furniture_requirements(
        brief_text,
        requirements,
    )

    extract_spatial_requirements(
        brief_text,
        requirements,
    )

    extract_preferences(
        brief_text,
        requirements,
    )

    extract_priorities(
        brief_text,
        requirements,
    )

    return requirements