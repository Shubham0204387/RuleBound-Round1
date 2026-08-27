from app.requirements import (
    Evidence,
    Preference,
    RequirementSet,
)


PREFERENCE_PATTERNS = [
    (
        "finish",
        "natural_oak",
        "natural oak",
    ),
    (
        "finish",
        "graphite",
        "graphite",
    ),
    (
        "finish",
        "durable_neutral",
        "durable neutral finishes",
    ),
    (
        "layout",
        "visually_open",
        "visually open",
    ),
    (
        "environment",
        "quiet_focus",
        "quiet focus",
    ),
    (
        "environment",
        "quiet_focus",
        "focus library",
    ),
]


def extract_preferences(
    text: str,
    requirements: RequirementSet,
):
    """Extract customer preferences without duplicates."""

    lower = text.lower()

    found_values = set()

    for category, value, phrase in PREFERENCE_PATTERNS:

        if (
            phrase in lower
            and value not in found_values
        ):

            requirements.preferences.append(
                Preference(
                    category=category,
                    value=value,
                    strength="preferred",
                    evidence=[
                        Evidence(
                            source="customer_brief",
                            text=phrase,
                        )
                    ],
                )
            )

            found_values.add(value)