from app.requirements import (
    Evidence,
    RequirementSet,
)

from app.extraction.capacity import extract_capacity
from app.extraction.furniture import extract_furniture_requirements
from app.extraction.spatial import extract_spatial_requirements
from app.extraction.preferences import extract_preferences
from app.extraction.priorities import extract_priorities


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