from app.layout.candidates import (
    generate_candidates,
)
from app.layout.zones import build_zones
from app.loader import load_all_data


def main():

    print("\n================================")
    print(" Candidate Position Test")
    print("================================")

    data = load_all_data()

    room = data["rooms"]["ROOM-01"]

    product = data["catalog"][
        "NW-DES-009"
    ]

    zones = build_zones(room)

    all_zones = (
        zones["usable"]
        + zones["perimeter"]
        + zones["open"]
        + zones["windows"]
        + zones["doors"]
        + zones["egress"]
    )

    candidates = generate_candidates(
        room=room,
        product=product,
        family="desk",
        finish_id="F01",
        zones=all_zones,
        catalog=data["catalog"],
        existing_placements=[],
        step_mm=300,
        max_candidates=20,
    )

    print("\nROOM:")
    print(room.room_id)

    print("\nPRODUCT:")
    print(
        product.sku,
        "|",
        product.name,
        "|",
        product.width_mm,
        "x",
        product.depth_mm,
    )

    print("\nCANDIDATES:")
    print(
        f"Generated: {len(candidates)}"
    )

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        placement = candidate.placement

        print(
            f"{index}. "
            f"{placement.placement_id} | "
            f"zone={candidate.zone_type} | "
            f"x={placement.x_mm} | "
            f"y={placement.y_mm} | "
            f"rotation={placement.rotation_deg}° | "
            f"score={candidate.strategy_score}"
        )

    print("\n================================")
    print(" CANDIDATE TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()