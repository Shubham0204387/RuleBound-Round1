from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection import select_product

from app.layout.assembler import assemble_layout


def main():

    print("\n================================")
    print(" Layout Assembly Test")
    print("================================")

    data = load_all_data()

    room_id = "ROOM-01"

    room = data["rooms"][room_id]

    brief = data["briefs"][room_id].text

    requirements = extract_requirements(
        room_id,
        brief,
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
            historical_jobs=data["historical_jobs"],
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

    layout = assembly.layout

    print("\nROOM:")
    print(room.room_id)

    print("\nPLACEMENTS:")
    print(
        f"Generated: {len(layout.placements)}"
    )

    for placement in layout.placements:

        product = data["catalog"][
            placement.sku
        ]

        print(
            f"{placement.placement_id} | "
            f"{placement.sku} | "
            f"{product.family} | "
            f"x={placement.x_mm} | "
            f"y={placement.y_mm} | "
            f"rotation={placement.rotation_deg}°"
        )

    print("\nUNRESOLVED:")

    if assembly.unresolved_families:

        for family in assembly.unresolved_families:
            print(f"  - {family}")

    else:
        print("  None")

    print("\nSTATUS:")
    print(layout.status)

    print("\n================================")
    print(" ASSEMBLY TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()