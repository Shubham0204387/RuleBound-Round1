from dataclasses import dataclass
from typing import List, Tuple


Point = Tuple[float, float]


@dataclass(frozen=True)
class Rectangle:
    x_mm: float
    y_mm: float
    width_mm: float
    depth_mm: float

    @property
    def left(self) -> float:
        return self.x_mm

    @property
    def right(self) -> float:
        return self.x_mm + self.width_mm

    @property
    def bottom(self) -> float:
        return self.y_mm

    @property
    def top(self) -> float:
        return self.y_mm + self.depth_mm

    @property
    def area_mm2(self) -> float:
        return max(0, self.width_mm) * max(0, self.depth_mm)

    @property
    def center(self) -> Point:
        return (
            self.x_mm + self.width_mm / 2,
            self.y_mm + self.depth_mm / 2,
        )

    def contains_point(self, point: Point) -> bool:
        x, y = point

        return (
            self.left <= x <= self.right
            and self.bottom <= y <= self.top
        )

    def contains_rectangle(
        self,
        other: "Rectangle",
    ) -> bool:

        return (
            other.left >= self.left
            and other.right <= self.right
            and other.bottom >= self.bottom
            and other.top <= self.top
        )

    def overlaps(
        self,
        other: "Rectangle",
    ) -> bool:

        return (
            self.left < other.right
            and self.right > other.left
            and self.bottom < other.top
            and self.top > other.bottom
        )

    def overlap_area(
        self,
        other: "Rectangle",
    ) -> float:

        overlap_width = max(
            0,
            min(self.right, other.right)
            - max(self.left, other.left),
        )

        overlap_depth = max(
            0,
            min(self.top, other.top)
            - max(self.bottom, other.bottom),
        )

        return overlap_width * overlap_depth

    def expanded(
        self,
        margin_mm: float,
    ) -> "Rectangle":

        return Rectangle(
            x_mm=self.x_mm - margin_mm,
            y_mm=self.y_mm - margin_mm,
            width_mm=self.width_mm + 2 * margin_mm,
            depth_mm=self.depth_mm + 2 * margin_mm,
        )


def footprint_for_rotation(
    x_mm: float,
    y_mm: float,
    width_mm: float,
    depth_mm: float,
    rotation_deg: int,
) -> Rectangle:

    normalized = rotation_deg % 360

    if normalized in (0, 180):
        width = width_mm
        depth = depth_mm

    elif normalized in (90, 270):
        width = depth_mm
        depth = width_mm

    else:
        raise ValueError(
            "Only 0°, 90°, 180° and 270° rotations "
            "are supported."
        )

    return Rectangle(
        x_mm=x_mm,
        y_mm=y_mm,
        width_mm=width,
        depth_mm=depth,
    )


def polygon_bounds(
    boundary_mm: List[List[float]],
) -> Rectangle:

    if not boundary_mm:
        raise ValueError(
            "Room boundary cannot be empty."
        )

    xs = [
        point[0]
        for point in boundary_mm
    ]

    ys = [
        point[1]
        for point in boundary_mm
    ]

    return Rectangle(
        x_mm=min(xs),
        y_mm=min(ys),
        width_mm=max(xs) - min(xs),
        depth_mm=max(ys) - min(ys),
    )


def point_inside_polygon(
    point: Point,
    boundary_mm: List[List[float]],
) -> bool:

    if len(boundary_mm) < 3:
        return False

    x, y = point

    inside = False

    j = len(boundary_mm) - 1

    for i in range(len(boundary_mm)):

        xi, yi = boundary_mm[i]
        xj, yj = boundary_mm[j]

        intersects = (
            (yi > y) != (yj > y)
            and x
            < (
                (xj - xi)
                * (y - yi)
                / ((yj - yi) or 1e-12)
                + xi
            )
        )

        if intersects:
            inside = not inside

        j = i

    return inside


def rectangle_inside_polygon(
    rectangle: Rectangle,
    boundary_mm: List[List[float]],
) -> bool:

    corners = [
        (rectangle.left, rectangle.bottom),
        (rectangle.right, rectangle.bottom),
        (rectangle.right, rectangle.top),
        (rectangle.left, rectangle.top),
    ]

    return all(
        point_inside_polygon(
            point,
            boundary_mm,
        )
        for point in corners
    )


def rectangle_inside_polygon_bounds(
    rectangle: Rectangle,
    boundary_mm: List[List[float]],
) -> bool:

    return rectangle_inside_polygon(
        rectangle,
        boundary_mm,
    )


def minimum_axis_clearance(
    first: Rectangle,
    second: Rectangle,
) -> float:

    horizontal = max(
        second.left - first.right,
        first.left - second.right,
        0,
    )

    vertical = max(
        second.bottom - first.top,
        first.bottom - second.top,
        0,
    )

    if horizontal == 0:
        return vertical

    if vertical == 0:
        return horizontal

    return min(
        horizontal,
        vertical,
    )