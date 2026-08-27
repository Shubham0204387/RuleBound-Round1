import re

from app.requirements import (
    Evidence,
    RequirementSet,
    SpatialRequirement,
)


def extract_spatial_requirements(
    text: str,
    requirements: RequirementSet,
):
    """Extract spatial requirements."""

    lower = text.lower()

    # Clear route

    match = re.search(
        r"clear route .*?to the ([^.]+)",
        lower,
    )

    if match:
        destination = match.group(1).strip()

        requirements.spatial.append(
            SpatialRequirement(
                requirement_type="clear_route",
                value=destination,
                priority="normal",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text=match.group(0),
                    )
                ],
            )
        )

    elif (
        "clear route" in lower
        or "clear circulation" in lower
    ):
        requirements.spatial.append(
            SpatialRequirement(
                requirement_type="clear_route",
                priority="normal",
                evidence=[
                    Evidence(
                        source="customer_brief",
                        text="clear route",
                    )
                ],
            )
        )

    # Other spatial requirements

    spatial_patterns = [
        (
            "generous_egress",
            [
                "generous egress",
                "egress path",
            ],
            "normal",
        ),
        (
            "accessible_circulation",
            [
                "accessible circulation",
            ],
            "normal",
        ),
        (
            "preserve_daylight",
            [
                "preserve daylight",
            ],
            "normal",
        ),
        (
            "protect_windows",
            [
                "windows must not be obstructed",
                "window must not be obstructed",
                "do not obstruct windows",
            ],
            "high",
        ),
        (
            "protect_doors",
            [
                "both doors must remain usable",
                "door must remain usable",
            ],
            "high",
        ),
        (
            "protect_egress",
            [
                "do not narrow the marked egress route",
                "prioritise the egress route",
                "no furniture may narrow the marked egress route",
            ],
            "high",
        ),
    ]

    for requirement_type, phrases, priority in spatial_patterns:

        for phrase in phrases:

            if phrase in lower:

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