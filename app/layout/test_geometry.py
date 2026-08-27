from app.layout.geometry import (
    Rectangle,
    footprint_for_rotation,
    minimum_axis_clearance,
    polygon_bounds,
)


def main():
    print("\n================================")
    print(" Layout Geometry Test")
    print("================================\n")

    first = Rectangle(
        x_mm=1000,
        y_mm=1000,
        width_mm=1200,
        depth_mm=600,
    )

    second = Rectangle(
        x_mm=2300,
        y_mm=1000,
        width_mm=1200,
        depth_mm=600,
    )

    overlapping = Rectangle(
        x_mm=1500,
        y_mm=1200,
        width_mm=1200,
        depth_mm=600,
    )

    print("FIRST:")
    print(first)

    print("\nSECOND:")
    print(second)

    print("\nOVERLAPPING:")
    print(overlapping)

    print("\nOverlap tests:")

    print(
        "first vs second:",
        first.overlaps(second),
    )

    print(
        "first vs overlapping:",
        first.overlaps(overlapping),
    )

    print("\nOverlap area:")

    print(
        "first vs second:",
        first.overlap_area(second),
    )

    print(
        "first vs overlapping:",
        first.overlap_area(overlapping),
    )

    print("\nClearance:")

    print(
        "first → second:",
        minimum_axis_clearance(
            first,
            second,
        ),
        "mm",
    )

    print("\nRotation:")

    rotated = footprint_for_rotation(
        x_mm=1000,
        y_mm=1000,
        width_mm=1200,
        depth_mm=600,
        rotation_deg=90,
    )

    print(
        "0° :",
        first.width_mm,
        "x",
        first.depth_mm,
    )

    print(
        "90°:",
        rotated.width_mm,
        "x",
        rotated.depth_mm,
    )

    print("\nRoom bounds:")

    boundary = [
        [0, 0],
        [7200, 0],
        [7200, 5400],
        [0, 5400],
    ]

    bounds = polygon_bounds(
        boundary
    )

    print(bounds)

    print(
        "\nInside room:",
        bounds.contains_rectangle(first),
    )

    print("\n================================")
    print(" GEOMETRY TEST PASSED")
    print("================================")


if __name__ == "__main__":
    main()