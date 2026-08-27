from app.layout.placement import (
    create_placement,
    get_product_footprint,
    placement_clearance,
    placement_inside_room,
    placement_overlap_area,
    placement_overlaps,
)
from app.loader import load_all_data


def main():
    print("\n================================")
    print(" Layout Placement Test")
    print("================================\n")

    data = load_all_data()

    room = data["rooms"]["ROOM-01"]

    first = create_placement(
        placement_id="P001",
        sku="NW-DES-009",
        finish_id="F01",
        x_mm=1000,
        y_mm=1000,
        rotation_deg=0,
    )

    second = create_placement(
        placement_id="P002",
        sku="NW-DES-009",
        finish_id="F01",
        x_mm=2300,
        y_mm=1000,
        rotation_deg=0,
    )

    overlapping = create_placement(
        placement_id="P003",
        sku="NW-DES-009",
        finish_id="F01",
        x_mm=1500,
        y_mm=1200,
        rotation_deg=0,
    )

    first_footprint = get_product_footprint(
        first,
        data["catalog"],
    )

    print("FIRST PLACEMENT:")
    print(first)

    print("\nFIRST FOOTPRINT:")
    print(first_footprint)

    print("\nOVERLAP TEST:")
    print(
        "P001 vs P002:",
        placement_overlaps(
            first,
            second,
            data["catalog"],
        ),
    )

    print(
        "P001 vs P003:",
        placement_overlaps(
            first,
            overlapping,
            data["catalog"],
        ),
    )

    print("\nOVERLAP AREA:")
    print(
        "P001 vs P003:",
        placement_overlap_area(
            first,
            overlapping,
            data["catalog"],
        ),
        "mm²",
    )

    print("\nCLEARANCE:")
    print(
        "P001 → P002:",
        placement_clearance(
            first,
            second,
            data["catalog"],
        ),
        "mm",
    )

    print("\nROOM CHECK:")
    print(
        "P001 inside ROOM-01:",
        placement_inside_room(
            first,
            room,
            data["catalog"],
        ),
    )

    print("\nROTATION TEST:")

    rotated = create_placement(
        placement_id="P004",
        sku="NW-DES-009",
        finish_id="F01",
        x_mm=1000,
        y_mm=1000,
        rotation_deg=90,
    )

    rotated_footprint = get_product_footprint(
        rotated,
        data["catalog"],
    )

    print(
        "0°:",
        first_footprint.width_mm,
        "x",
        first_footprint.depth_mm,
    )

    print(
        "90°:",
        rotated_footprint.width_mm,
        "x",
        rotated_footprint.depth_mm,
    )

    print("\n================================")
    print(" PLACEMENT TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()