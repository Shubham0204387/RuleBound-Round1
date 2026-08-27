from app.loader import load_all_data
from app.extraction import extract_requirements


def main():
    data = load_all_data()

    print("\n================================")
    print(" Requirement Extraction Test")
    print("================================\n")

    for room_id in sorted(data["briefs"]):

        brief = data["briefs"][room_id]

        result = extract_requirements(
            room_id,
            brief.text,
        )

        print(f"===== {room_id} =====")
        print(f"Capacity: {result.capacity}")

        print("Furniture:")
        for item in result.furniture:
            print(
                f"  - {item.family}: "
                f"quantity={item.quantity}, "
                f"attributes={item.attributes}"
            )

        print("Spatial:")
        for item in result.spatial:
            print(
                f"  - {item.requirement_type}: "
                f"priority={item.priority}"
            )

        print("Preferences:")
        for item in result.preferences:
            print(
                f"  - {item.category}: "
                f"{item.value}"
            )

        print("Priorities:")
        for item in result.priorities:
            print(
                f"  - {item.higher_priority} > "
                f"{item.lower_priority}"
            )

        print()


if __name__ == "__main__":
    main()