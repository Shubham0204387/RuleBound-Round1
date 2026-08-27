from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection.selector import select_product


def main():

    data = load_all_data()

    print("\n================================")
    print(" Final Product Selection Test")
    print("================================\n")

    for room_id in sorted(
        data["briefs"]
    ):

        brief = data["briefs"][room_id]

        extracted = extract_requirements(
            room_id,
            brief.text,
        )

        resolved = resolve_requirements(
            extracted
        )

        print(
            f"===== {room_id} ====="
        )

        for requirement in resolved.furniture:

            result = select_product(
                room_id=room_id,
                requirement=requirement,
                catalog=data["catalog"],
                historical_jobs=data[
                    "historical_jobs"
                ],
            )

            print(
                f"\n{requirement.family}: "
                f"quantity={requirement.quantity} "
                f"status={requirement.quantity_status}"
            )

            if result.selected is None:

                print(
                    "  No valid product candidate."
                )

                continue

            selected = result.selected
            candidate = selected.candidate
            score = selected.breakdown

            print(
                f"  Selected: {candidate.sku}"
            )

            print(
                f"  Name: {candidate.name}"
            )

            print(
                f"  Price: ₹"
                f"{candidate.list_price_inr:,}"
            )

            print(
                f"  Score: "
                f"{score.total:.4f}"
            )

            print(
                f"  Historical usage: "
                f"{candidate.historical_quantity}"
            )

            print(
                "  Alternatives:"
            )

            for alternative in (
                result.alternatives
            ):

                print(
                    f"    - "
                    f"{alternative.candidate.sku} "
                    f"("
                    f"{alternative.breakdown.total:.4f}"
                    f")"
                )

        print()


if __name__ == "__main__":
    main()