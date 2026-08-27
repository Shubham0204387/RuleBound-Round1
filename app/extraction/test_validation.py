from app.loader import load_all_data
from app.extraction import extract_requirements
from app.extraction.validator import validate_requirements


def main():

    data = load_all_data()

    print("\n================================")
    print(" Requirement Validation Test")
    print("================================\n")

    total_issues = 0

    for room_id in sorted(data["briefs"]):

        brief = data["briefs"][room_id]

        requirements = extract_requirements(
            room_id,
            brief.text,
        )

        validation = validate_requirements(
            requirements
        )

        print(f"===== {room_id} =====")

        if validation.valid:
            print("Status: VALID")

        else:
            print("Status: INVALID")

        if validation.issues:

            for issue in validation.issues:

                print(
                    f"  - [{issue.severity.upper()}] "
                    f"{issue.issue_type}: "
                    f"{issue.message}"
                )

            total_issues += len(
                validation.issues
            )

        else:
            print("  No issues found.")

        print()

    print("================================")

    if total_issues == 0:
        print("ALL REQUIREMENT CHECKS PASSED")
    else:
        print(
            f"TOTAL ISSUES FOUND: {total_issues}"
        )


if __name__ == "__main__":
    main()