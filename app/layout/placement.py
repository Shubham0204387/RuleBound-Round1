from typing import Dict, Tuple

from app.layout.geometry import (
    Rectangle,
    footprint_for_rotation,
)
from app.layout.models import Placement


def get_product_footprint(
    placement: Placement,
    catalog,
) -> Rectangle:
    product = catalog[placement.sku]

    return footprint_for_rotation(
        x_mm=placement.x_mm,
        y_mm=placement.y_mm,
        width_mm=product.width_mm,
        depth_mm=product.depth_mm,
        rotation_deg=placement.rotation_deg,
    )


def create_placement(
    placement_id: str,
    sku: str,
    finish_id: str,
    x_mm: int,
    y_mm: int,
    rotation_deg: int = 0,
) -> Placement:

    return Placement(
        placement_id=placement_id,
        sku=sku,
        finish_id=finish_id,
        x_mm=x_mm,
        y_mm=y_mm,
        rotation_deg=rotation_deg,
    )


def placement_overlaps(
    first: Placement,
    second: Placement,
    catalog,
) -> bool:

    first_footprint = get_product_footprint(
        first,
        catalog,
    )

    second_footprint = get_product_footprint(
        second,
        catalog,
    )

    return first_footprint.overlaps(
        second_footprint
    )


def placement_overlap_area(
    first: Placement,
    second: Placement,
    catalog,
) -> float:

    first_footprint = get_product_footprint(
        first,
        catalog,
    )

    second_footprint = get_product_footprint(
        second,
        catalog,
    )

    return first_footprint.overlap_area(
        second_footprint
    )


def placement_inside_room(
    placement: Placement,
    room,
    catalog,
) -> bool:

    footprint = get_product_footprint(
        placement,
        catalog,
    )

    min_x = min(
        point[0]
        for point in room.boundary_mm
    )

    max_x = max(
        point[0]
        for point in room.boundary_mm
    )

    min_y = min(
        point[1]
        for point in room.boundary_mm
    )

    max_y = max(
        point[1]
        for point in room.boundary_mm
    )

    return (
        footprint.left >= min_x
        and footprint.right <= max_x
        and footprint.bottom >= min_y
        and footprint.top <= max_y
    )


def placement_clearance(
    first: Placement,
    second: Placement,
    catalog,
) -> float:

    first_footprint = get_product_footprint(
        first,
        catalog,
    )

    second_footprint = get_product_footprint(
        second,
        catalog,
    )

    from app.layout.geometry import minimum_axis_clearance

    return minimum_axis_clearance(
        first_footprint,
        second_footprint,
    )