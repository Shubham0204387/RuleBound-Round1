from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection.candidates import build_candidates


def main():

    data = load_all_data()

    print("\n================================")
    print(" Product Candidate Test")
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

            result = build_candidates(
                room_id=room_id,
                requirement=requirement,
                catalog=data["catalog"],
                historical_jobs=data["historical_jobs"],
            )

            print(
                f"\n{requirement.family}: "
                f"quantity={requirement.quantity}, "
                f"status={requirement.quantity_status}"
            )

            print(
                f"  Candidates: "
                f"{len(result.candidates)}"
            )

            print(
                f"  Rejected: "
                f"{len(result.rejected)}"
            )

            print("  First 5 candidates:")

            for candidate in (
                result.candidates[:5]
            ):

                print(
                    f"    {candidate.sku} | "
                    f"{candidate.name} | "
                    f"₹{candidate.list_price_inr:,}"
                )

        print()


if __name__ == "__main__":
    main()