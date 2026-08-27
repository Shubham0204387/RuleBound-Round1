from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection.candidates import build_candidates
from app.selection.scorer import (
    score_candidates,
    rank_candidates,
)


def main():

    data = load_all_data()

    print("\n================================")
    print(" Product Scoring Test")
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

            candidate_set = build_candidates(
                room_id=room_id,
                requirement=requirement,
                catalog=data["catalog"],
                historical_jobs=data[
                    "historical_jobs"
                ],
            )

            scored = score_candidates(
                candidate_set.candidates
            )

            ranked = rank_candidates(
                scored
            )

            print(
                f"\n{requirement.family}: "
                f"quantity={requirement.quantity}"
            )

            print(
                "  Top 5:"
            )

            for rank, item in enumerate(
                ranked[:5],
                start=1,
            ):

                candidate = item.candidate
                score = item.breakdown

                print(
                    f"    {rank}. "
                    f"{candidate.sku} | "
                    f"₹{candidate.list_price_inr:,} | "
                    f"score={score.total:.4f} | "
                    f"historical="
                    f"{candidate.historical_quantity}"
                )

        print()


if __name__ == "__main__":
    main()
    