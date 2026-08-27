from app.requirements import (
    Evidence,
    RequirementIssue,
    RequirementSet,
    RequirementValidation,
)


def validate_capacity(
    requirements: RequirementSet,
    issues: list,
):
    """Validate room capacity."""

    if requirements.capacity is None:

        issues.append(
            RequirementIssue(
                issue_type="missing_capacity",
                message=(
                    "The customer brief does not specify "
                    "room capacity."
                ),
                severity="warning",
            )
        )

    elif requirements.capacity <= 0:

        issues.append(
            RequirementIssue(
                issue_type="invalid_capacity",
                message=(
                    "Room capacity must be greater than zero."
                ),
                severity="error",
            )
        )


def validate_furniture(
    requirements: RequirementSet,
    issues: list,
):
    """Validate furniture requirements."""

    for item in requirements.furniture:

        if not item.family:

            issues.append(
                RequirementIssue(
                    issue_type="missing_family",
                    message=(
                        "A furniture requirement has no family."
                    ),
                    severity="error",
                )
            )

        if item.quantity is not None and item.quantity <= 0:

            issues.append(
                RequirementIssue(
                    issue_type="invalid_quantity",
                    message=(
                        f"{item.family}: quantity must "
                        f"be greater than zero."
                    ),
                    severity="error",
                )
            )

        if (
            item.movable is True
            and item.fixed is True
        ):

            issues.append(
                RequirementIssue(
                    issue_type="contradictory_mobility",
                    message=(
                        f"{item.family}: item cannot be "
                        f"both movable and fixed."
                    ),
                    severity="error",
                )
            )


def validate_duplicates(
    requirements: RequirementSet,
    issues: list,
):
    """Detect duplicate furniture requirements."""

    seen = set()

    for item in requirements.furniture:

        key = (
            item.family,
            item.quantity,
            tuple(sorted(item.attributes)),
            item.movable,
            item.fixed,
        )

        if key in seen:

            issues.append(
                RequirementIssue(
                    issue_type="duplicate_requirement",
                    message=(
                        f"Duplicate furniture requirement "
                        f"detected for {item.family}."
                    ),
                    severity="warning",
                )
            )

        seen.add(key)


def validate_priorities(
    requirements: RequirementSet,
    issues: list,
):
    """Validate customer priorities."""

    for priority in requirements.priorities:

        if (
            priority.higher_priority
            == priority.lower_priority
        ):

            issues.append(
                RequirementIssue(
                    issue_type="invalid_priority",
                    message=(
                        "A priority cannot prefer a "
                        "criterion over itself."
                    ),
                    severity="error",
                )
            )


def validate_spatial_requirements(
    requirements: RequirementSet,
    issues: list,
):
    """Validate spatial requirements."""

    for item in requirements.spatial:

        if not item.requirement_type:

            issues.append(
                RequirementIssue(
                    issue_type="missing_spatial_type",
                    message=(
                        "A spatial requirement has no type."
                    ),
                    severity="error",
                )
            )


def validate_requirements(
    requirements: RequirementSet,
) -> RequirementValidation:
    """
    Validate a RequirementSet without changing it.

    Important:
    This function only identifies issues.
    It does not invent or modify requirements.
    """

    issues = []

    validate_capacity(
        requirements,
        issues,
    )

    validate_furniture(
        requirements,
        issues,
    )

    validate_duplicates(
        requirements,
        issues,
    )

    validate_priorities(
        requirements,
        issues,
    )

    validate_spatial_requirements(
        requirements,
        issues,
    )

    has_errors = any(
        issue.severity == "error"
        for issue in issues
    )

    return RequirementValidation(
        valid=not has_errors,
        issues=issues,
    )