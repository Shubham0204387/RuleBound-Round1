from app.layout.zones import build_zones
from app.loader import load_all_data


def main():
    print("\n================================")
    print(" Room Zone Identification Test")
    print("================================")

    data = load_all_data()

    for room_id, room in data["rooms"].items():

        print(f"\n===== {room_id} =====")
        print(f"Name: {room.name}")
        print(
            f"Boundary points: "
            f"{len(room.boundary_mm)}"
        )

        zones = build_zones(room)

        for category, items in zones.items():

            print(
                f"\n{category.upper()}:"
            )

            if not items:
                print("  None")
                continue

            for zone in items:
                print(
                    f"  {zone.zone_id}"
                    f" | type={zone.zone_type}"
                    f" | x={zone.x_mm}"
                    f" | y={zone.y_mm}"
                    f" | width={zone.width_mm}"
                    f" | depth={zone.depth_mm}"
                    f" | priority={zone.priority}"
                )

    print("\n================================")
    print(" ZONE IDENTIFICATION PASSED")
    print("================================")


if __name__ == "__main__":
    main()