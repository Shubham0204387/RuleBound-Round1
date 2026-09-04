import re

from app.requirements import (
    Evidence,
    FurnitureRequirement,
    RequirementSet,
)

from app.extraction.helpers import number_from_text


def add_furniture(
    requirements: RequirementSet,
    family: str,
    quantity,
    attributes=None,
    evidence_text="",
    movable=None,
    fixed=None,
):
    """Add one furniture requirement."""

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


def extract_desks(text, requirements):
    """Extract desk/work-position requirements."""

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


    match = re.search(
        r"(eight|seven|six|five|four|three|two|one|\d+)"
        r"\s+fixed\s+work\s+positions?",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="desk",
            quantity=quantity,
            attributes=["work_position"],
            fixed=True,
            evidence_text=match.group(0),
        )

    # Numeric desk positions
    match = re.search(
        r"(twenty|nineteen|eighteen|seventeen|sixteen|fifteen|fourteen|"
        r"thirteen|twelve|eleven|ten|nine|eight|seven|six|five|four|"
        r"three|two|one|\d+)\s+desk\s+positions?",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="desk",
            quantity=quantity,
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


def extract_seating(text, requirements):
    """Extract chair/seating requirements."""

    lower = text.lower()

    # Ergonomic chairs
    if "ergonomic chair" in lower or "ergonomic chairs" in lower:
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["ergonomic"],
            evidence_text="ergonomic chairs",
        )

    # Movable task seating
    if "movable task seating" in lower:
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["task"],
            movable=True,
            evidence_text="movable task seating",
        )

    # Generic task seating
    elif "task seating" in lower:
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["task"],
            evidence_text="task seating",
        )

    # Numeric seating
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

    # Written-number seating:
    # "seating for all ten"
    match = re.search(
        r"seating\s+for\s+all\s+"
        r"(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
        r"seventeen|eighteen|nineteen|twenty)",
        lower,
    )

    if match:
        quantity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="chair",
            quantity=quantity,
            attributes=["seating"],
            evidence_text=match.group(0),
        )

    # Generic chair fallback
    if (
        "chair" in lower
        and not any(
            item.family == "chair"
            for item in requirements.furniture
        )
    ):
        add_furniture(
            requirements,
            family="chair",
            quantity=None,
            attributes=["task"],
            evidence_text="chairs",
        )


def extract_storage(text, requirements):
    """Extract storage requirements."""

    lower = text.lower()

    # Lockable storage
    match = re.search(
        r"(\d+|one|two|three|four|five)\s+"
        r"lockable\s+storage\s+units?",
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

    # Generic storage fallback
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


def extract_collaboration(text, requirements):
    """Extract collaboration furniture requirements."""

    lower = text.lower()

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

    # Collaboration zones
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
        capacity = number_from_text(match.group(1))

        add_furniture(
            requirements,
            family="collaboration",
            quantity=1,
            attributes=[
                "touchdown",
                f"capacity_{capacity}",
            ],
            evidence_text=match.group(0),
        )


def extract_accessories(text, requirements):
    """Extract accessory requirements."""

    lower = text.lower()

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


def extract_furniture_requirements(
    text: str,
    requirements: RequirementSet,
):
    """Run all furniture-specific extractors."""

    extract_desks(text, requirements)
    extract_seating(text, requirements)
    extract_storage(text, requirements)
    extract_collaboration(text, requirements)
    extract_accessories(text, requirements)