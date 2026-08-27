from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements


def main():

    data = load_all_data()

    print("\n================================")
    print(" Requirement Resolution Test")
    print("================================\n")

    for room_id in sorted(data["briefs"]):

        brief = data["briefs"][room_id]

        extracted = extract_requirements(
            room_id,
            brief.text,
        )

        resolved = resolve_requirements(
            extracted
        )

        print(f"===== {room_id} =====")
        print(f"Capacity: {resolved.capacity}")

        print("Furniture:")

        for item in resolved.furniture:

            print(
                f"  - {item.family}: "
                f"quantity={item.quantity}, "
                f"status={item.quantity_status}, "
                f"attributes={item.attributes}"
            )

            for evidence in item.evidence:

                print(
                    f"      reason: "
                    f"{evidence.reason}"
                )

        print()


if __name__ == "__main__":
    main()