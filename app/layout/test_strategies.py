from app.layout.strategies import (
    choose_best_rotation,
    get_placement_order,
    get_strategy,
    placement_score,
    strategy_summary,
)


def main():

    print("\n================================")
    print(" Placement Strategy Test")
    print("================================\n")

    families = [
        "desk",
        "chair",
        "storage",
        "collaboration",
        "accessory",
    ]

    print("PLACEMENT ORDER")
    print("----------------")

    order = get_placement_order(
        families
    )

    for index, family in enumerate(
        order,
        start=1,
    ):
        print(
            f"{index}. {family}"
        )

    print("\nSTRATEGIES")
    print("----------")

    for line in strategy_summary():
        print(line)

    print("\nROTATION PREFERENCES")
    print("--------------------")

    for family in families:

        rotation = choose_best_rotation(
            family,
            [0, 90, 180, 270],
        )

        print(
            f"{family}: {rotation}°"
        )

    print("\nZONE SCORING")
    print("------------")

    tests = [
        ("desk", "work_zone"),
        ("desk", "egress"),
        ("storage", "perimeter"),
        ("collaboration", "open_zone"),
        ("chair", "main_circulation"),
    ]

    for family, zone in tests:

        score = placement_score(
            family,
            zone,
        )

        print(
            f"{family} → {zone}: {score}"
        )

    print("\nBLOCKED TEST")
    print("------------")

    print(
        "desk → work_zone:",
        placement_score(
            "desk",
            "work_zone",
            blocked=True,
        ),
    )

    print("\nDEFAULT FAMILY TEST")
    print("-------------------")

    default = get_strategy(
        "unknown_family"
    )

    print(default)

    print("\n================================")
    print(" STRATEGY TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()