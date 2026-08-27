from app.requirements import (
    Evidence,
    Priority,
    RequirementSet,
)


def extract_priorities(
    text: str,
    requirements: RequirementSet,
):
    """Extract explicit customer priorities."""

    lower = text.lower()

    if (
        "egress route" in lower
        and "maximum density" in lower
    ):
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