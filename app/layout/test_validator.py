from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection import select_product

from app.layout.assembler import assemble_layout
from app.layout.validator import validate_layout


def main():

    print("\n================================")
    print(" Layout Rule Validation Test")
    print("================================")

    data = load_all_data()

    room_id = "ROOM-01"

    room = data["rooms"][room_id]

    requirements = extract_requirements(
        room_id,
        data["briefs"][room_id].text,
    )

    resolved = resolve_requirements(
        requirements
    )

    selected_products = {}

    for requirement in resolved.furniture:

        result = select_product(
            room_id=room_id,
            requirement=requirement,
            catalog=data["catalog"],
            historical_jobs=data[
                "historical_jobs"
            ],
        )

        if result.selected is None:
            continue

        sku = result.selected.candidate.sku

        selected_products[
            requirement.family
        ] = data["catalog"][sku]

    assembly = assemble_layout(
        room=room,
        selected_products=selected_products,
        requirements=resolved,
        catalog=data["catalog"],
        finish_id="F01",
        step_mm=300,
        candidates_per_item=30,
    )

    validated = validate_layout(
        layout=assembly.layout,
        room=room,
        catalog=data["catalog"],
    )

    print("\nROOM:")
    print(room.room_id)

    print("\nPLACEMENTS:")
    print(
        len(validated.placements)
    )

    print("\nVALIDATION STATUS:")
    print(validated.status.upper())

    print("\nVIOLATIONS:")

    if not validated.violations:

        print("  None")

    else:

        for violation in validated.violations:

            print(
                f"\n  {violation.violation_id}"
            )

            print(
                f"    Rule: "
                f"{violation.rule_id}"
            )

            print(
                f"    Message: "
                f"{violation.message}"
            )

            print(
                f"    Affected: "
                f"{violation.affected_placement_ids}"
            )

            print(
                f"    Measured: "
                f"{violation.measured}"
            )

            print(
                f"    Required: "
                f"{violation.required}"
            )

    print("\n================================")
    print(" VALIDATION TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()