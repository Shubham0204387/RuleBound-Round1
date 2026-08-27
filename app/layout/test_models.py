from app.layout import (
    Layout,
    Placement,
    RepairOption,
    Violation,
)


def main():
    print("\n================================")
    print(" Layout Models Test")
    print("================================\n")

    placement = Placement(
        placement_id="P001",
        sku="NW-DES-009",
        finish_id="F01",
        x_mm=1200,
        y_mm=1200,
        rotation_deg=0,
    )

    repair = RepairOption(
        action="move",
        description="Move placement 300 mm east.",
        score=0.92,
        parameters={
            "dx_mm": 300,
            "dy_mm": 0,
        },
    )

    violation = Violation(
        violation_id="V001",
        rule_id="RB-GEO-006",
        message="Furniture footprints may not overlap.",
        affected_placement_ids=[
            "P001",
            "P002",
        ],
        measured={
            "overlap_mm2": 120000,
        },
        required={
            "overlap_mm2": 0,
        },
        repair_options=[
            repair,
        ],
    )

    layout = Layout(
        room_id="ROOM-01",
        placements=[
            placement,
        ],
        violations=[
            violation,
        ],
        status="invalid",
    )

    print("Placement:")
    print(placement)

    print("\nViolation:")
    print(violation)

    print("\nLayout:")
    print(layout)

    print("\nLayout dictionary:")
    print(layout.to_dict())

    print("\nValidity:")
    print("is_valid:", layout.is_valid())
    print("is_unsatisfiable:", layout.is_unsatisfiable())

    print("\n================================")
    print(" MODEL TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()