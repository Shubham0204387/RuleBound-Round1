from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Zone:
    zone_id: str
    zone_type: str
    x_mm: int
    y_mm: int
    width_mm: int
    depth_mm: int
    priority: int = 0

    @property
    def right_mm(self) -> int:
        return self.x_mm + self.width_mm

    @property
    def bottom_mm(self) -> int:
        return self.y_mm + self.depth_mm

    @property
    def area_mm2(self) -> int:
        return max(0, self.width_mm) * max(0, self.depth_mm)

    @property
    def center_x_mm(self) -> float:
        return self.x_mm + self.width_mm / 2

    @property
    def center_y_mm(self) -> float:
        return self.y_mm + self.depth_mm / 2


def _bounds(room):
    xs = [point[0] for point in room.boundary_mm]
    ys = [point[1] for point in room.boundary_mm]

    return (
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    )


def _clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def _clamp_zone(
    x_mm,
    y_mm,
    width_mm,
    depth_mm,
    room,
):
    min_x, min_y, max_x, max_y = _bounds(room)

    x_mm = _clamp(
        x_mm,
        min_x,
        max_x,
    )

    y_mm = _clamp(
        y_mm,
        min_y,
        max_y,
    )

    width_mm = min(
        width_mm,
        max_x - x_mm,
    )

    depth_mm = min(
        depth_mm,
        max_y - y_mm,
    )

    return (
        int(x_mm),
        int(y_mm),
        int(max(0, width_mm)),
        int(max(0, depth_mm)),
    )


def create_usable_zone(room) -> Zone:
    min_x, min_y, max_x, max_y = _bounds(room)

    return Zone(
        zone_id=f"{room.room_id}-usable",
        zone_type="usable_zone",
        x_mm=min_x,
        y_mm=min_y,
        width_mm=max_x - min_x,
        depth_mm=max_y - min_y,
        priority=1,
    )


def create_perimeter_zones(
    room,
    perimeter_mm: int = 600,
) -> List[Zone]:

    min_x, min_y, max_x, max_y = _bounds(room)

    width = max_x - min_x
    depth = max_y - min_y

    return [
        Zone(
            zone_id=f"{room.room_id}-perimeter-north",
            zone_type="perimeter",
            x_mm=min_x,
            y_mm=max_y - perimeter_mm,
            width_mm=width,
            depth_mm=perimeter_mm,
            priority=2,
        ),
        Zone(
            zone_id=f"{room.room_id}-perimeter-south",
            zone_type="perimeter",
            x_mm=min_x,
            y_mm=min_y,
            width_mm=width,
            depth_mm=perimeter_mm,
            priority=2,
        ),
        Zone(
            zone_id=f"{room.room_id}-perimeter-west",
            zone_type="perimeter",
            x_mm=min_x,
            y_mm=min_y + perimeter_mm,
            width_mm=perimeter_mm,
            depth_mm=max(
                0,
                depth - 2 * perimeter_mm,
            ),
            priority=2,
        ),
        Zone(
            zone_id=f"{room.room_id}-perimeter-east",
            zone_type="perimeter",
            x_mm=max_x - perimeter_mm,
            y_mm=min_y + perimeter_mm,
            width_mm=perimeter_mm,
            depth_mm=max(
                0,
                depth - 2 * perimeter_mm,
            ),
            priority=2,
        ),
    ]


def create_open_zone(
    room,
    perimeter_mm: int = 600,
) -> Zone:

    min_x, min_y, max_x, max_y = _bounds(room)

    return Zone(
        zone_id=f"{room.room_id}-open",
        zone_type="open_zone",
        x_mm=min_x + perimeter_mm,
        y_mm=min_y + perimeter_mm,
        width_mm=max(
            0,
            (max_x - min_x) - 2 * perimeter_mm,
        ),
        depth_mm=max(
            0,
            (max_y - min_y) - 2 * perimeter_mm,
        ),
        priority=3,
    )


def create_window_zones(room) -> List[Zone]:

    zones = []

    max_x = max(
        point[0]
        for point in room.boundary_mm
    )

    max_y = max(
        point[1]
        for point in room.boundary_mm
    )

    for index, window in enumerate(
        room.windows,
        start=1,
    ):
        wall = window.get("wall")
        offset = window.get("offset_mm", 0)
        width = window.get("width_mm", 0)

        if wall == "north":
            x_mm = offset
            y_mm = max_y - 900
            zone_width = width
            zone_depth = 900

        elif wall == "south":
            x_mm = offset
            y_mm = 0
            zone_width = width
            zone_depth = 900

        elif wall == "east":
            x_mm = max_x - 900
            y_mm = offset
            zone_width = 900
            zone_depth = width

        elif wall == "west":
            x_mm = 0
            y_mm = offset
            zone_width = 900
            zone_depth = width

        else:
            continue

        (
            x_mm,
            y_mm,
            zone_width,
            zone_depth,
        ) = _clamp_zone(
            x_mm,
            y_mm,
            zone_width,
            zone_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=f"{room.room_id}-window-{index}",
                zone_type="window_protection_zone",
                x_mm=x_mm,
                y_mm=y_mm,
                width_mm=zone_width,
                depth_mm=zone_depth,
                priority=0,
            )
        )

    return zones


def create_door_zones(room) -> List[Zone]:

    zones = []

    min_x, min_y, max_x, max_y = _bounds(room)

    for index, door in enumerate(
        room.doors,
        start=1,
    ):
        wall = door.get("wall")
        offset = door.get("offset_mm", 0)
        width = door.get("width_mm", 0)

        if wall == "south":
            x_mm = offset
            y_mm = min_y
            zone_width = width
            zone_depth = 850

        elif wall == "north":
            x_mm = offset
            y_mm = max_y - 850
            zone_width = width
            zone_depth = 850

        elif wall == "west":
            x_mm = min_x
            y_mm = offset
            zone_width = 850
            zone_depth = width

        elif wall == "east":
            x_mm = max_x - 850
            y_mm = offset
            zone_width = 850
            zone_depth = width

        else:
            continue

        (
            x_mm,
            y_mm,
            zone_width,
            zone_depth,
        ) = _clamp_zone(
            x_mm,
            y_mm,
            zone_width,
            zone_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=f"{room.room_id}-door-{index}",
                zone_type="door_swing",
                x_mm=x_mm,
                y_mm=y_mm,
                width_mm=zone_width,
                depth_mm=zone_depth,
                priority=0,
            )
        )

    return zones


def create_egress_zones(
    room,
    egress_width_mm: int = 1100,
) -> List[Zone]:

    egress = room.egress

    if not egress:
        return []

    door_id = egress.get("from_door_id")
    target = egress.get("to_point_mm")

    if not target:
        return []

    door = None

    for candidate in room.doors:
        if candidate.get("door_id") == door_id:
            door = candidate
            break

    if door is None:
        return []

    min_x, min_y, max_x, max_y = _bounds(room)

    door_wall = door.get("wall")
    offset = door.get("offset_mm", 0)
    door_width = door.get("width_mm", 0)

    target_x = _clamp(
        target[0],
        min_x,
        max_x,
    )

    target_y = _clamp(
        target[1],
        min_y,
        max_y,
    )

    zones = []

    if door_wall == "south":

        door_center_x = (
            offset + door_width / 2
        )

        horizontal_x = (
            min(
                door_center_x,
                target_x,
            )
            - egress_width_mm / 2
        )

        horizontal_width = (
            abs(
                target_x
                - door_center_x
            )
            + egress_width_mm
        )

        horizontal_y = min_y

        (
            horizontal_x,
            horizontal_y,
            horizontal_width,
            horizontal_depth,
        ) = _clamp_zone(
            horizontal_x,
            horizontal_y,
            horizontal_width,
            egress_width_mm,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-horizontal"
                ),
                zone_type="egress",
                x_mm=horizontal_x,
                y_mm=horizontal_y,
                width_mm=horizontal_width,
                depth_mm=horizontal_depth,
                priority=0,
            )
        )

        vertical_x = (
            target_x
            - egress_width_mm / 2
        )

        vertical_y = min_y

        vertical_depth = (
            target_y - min_y
        )

        (
            vertical_x,
            vertical_y,
            vertical_width,
            vertical_depth,
        ) = _clamp_zone(
            vertical_x,
            vertical_y,
            egress_width_mm,
            vertical_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-vertical"
                ),
                zone_type="egress",
                x_mm=vertical_x,
                y_mm=vertical_y,
                width_mm=vertical_width,
                depth_mm=vertical_depth,
                priority=0,
            )
        )

    elif door_wall == "north":

        door_center_x = (
            offset + door_width / 2
        )

        horizontal_x = (
            min(
                door_center_x,
                target_x,
            )
            - egress_width_mm / 2
        )

        horizontal_width = (
            abs(
                target_x
                - door_center_x
            )
            + egress_width_mm
        )

        horizontal_y = (
            max_y - egress_width_mm
        )

        (
            horizontal_x,
            horizontal_y,
            horizontal_width,
            horizontal_depth,
        ) = _clamp_zone(
            horizontal_x,
            horizontal_y,
            horizontal_width,
            egress_width_mm,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-horizontal"
                ),
                zone_type="egress",
                x_mm=horizontal_x,
                y_mm=horizontal_y,
                width_mm=horizontal_width,
                depth_mm=horizontal_depth,
                priority=0,
            )
        )

        vertical_x = (
            target_x
            - egress_width_mm / 2
        )

        vertical_y = target_y

        vertical_depth = (
            max_y - target_y
        )

        (
            vertical_x,
            vertical_y,
            vertical_width,
            vertical_depth,
        ) = _clamp_zone(
            vertical_x,
            vertical_y,
            egress_width_mm,
            vertical_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-vertical"
                ),
                zone_type="egress",
                x_mm=vertical_x,
                y_mm=vertical_y,
                width_mm=vertical_width,
                depth_mm=vertical_depth,
                priority=0,
            )
        )

    elif door_wall == "west":

        door_center_y = (
            offset + door_width / 2
        )

        vertical_y = (
            min(
                door_center_y,
                target_y,
            )
            - egress_width_mm / 2
        )

        vertical_depth = (
            abs(
                target_y
                - door_center_y
            )
            + egress_width_mm
        )

        vertical_x = min_x

        (
            vertical_x,
            vertical_y,
            vertical_width,
            vertical_depth,
        ) = _clamp_zone(
            vertical_x,
            vertical_y,
            egress_width_mm,
            vertical_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-vertical"
                ),
                zone_type="egress",
                x_mm=vertical_x,
                y_mm=vertical_y,
                width_mm=vertical_width,
                depth_mm=vertical_depth,
                priority=0,
            )
        )

        horizontal_x = min_x

        horizontal_y = (
            target_y
            - egress_width_mm / 2
        )

        horizontal_width = (
            target_x - min_x
        )

        (
            horizontal_x,
            horizontal_y,
            horizontal_width,
            horizontal_depth,
        ) = _clamp_zone(
            horizontal_x,
            horizontal_y,
            horizontal_width,
            egress_width_mm,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-horizontal"
                ),
                zone_type="egress",
                x_mm=horizontal_x,
                y_mm=horizontal_y,
                width_mm=horizontal_width,
                depth_mm=horizontal_depth,
                priority=0,
            )
        )

    elif door_wall == "east":

        door_center_y = (
            offset + door_width / 2
        )

        vertical_y = (
            min(
                door_center_y,
                target_y,
            )
            - egress_width_mm / 2
        )

        vertical_depth = (
            abs(
                target_y
                - door_center_y
            )
            + egress_width_mm
        )

        vertical_x = (
            max_x - egress_width_mm
        )

        (
            vertical_x,
            vertical_y,
            vertical_width,
            vertical_depth,
        ) = _clamp_zone(
            vertical_x,
            vertical_y,
            egress_width_mm,
            vertical_depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-vertical"
                ),
                zone_type="egress",
                x_mm=vertical_x,
                y_mm=vertical_y,
                width_mm=vertical_width,
                depth_mm=vertical_depth,
                priority=0,
            )
        )

        horizontal_x = target_x

        horizontal_y = (
            target_y
            - egress_width_mm / 2
        )

        horizontal_width = (
            max_x - target_x
        )

        (
            horizontal_x,
            horizontal_y,
            horizontal_width,
            horizontal_depth,
        ) = _clamp_zone(
            horizontal_x,
            horizontal_y,
            horizontal_width,
            egress_width_mm,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    "-egress-horizontal"
                ),
                zone_type="egress",
                x_mm=horizontal_x,
                y_mm=horizontal_y,
                width_mm=horizontal_width,
                depth_mm=horizontal_depth,
                priority=0,
            )
        )

    return zones


def create_walkway_zones(
    room,
    egress_zones: List[Zone],
    walkway_width_mm: int = 900,
) -> List[Zone]:

    zones = []

    for egress_zone in egress_zones:

        horizontal = (
            egress_zone.width_mm
            >= egress_zone.depth_mm
        )

        if horizontal:

            width = egress_zone.width_mm

            depth = min(
                walkway_width_mm,
                egress_zone.depth_mm,
            )

            x_mm = egress_zone.x_mm
            y_mm = egress_zone.y_mm

            direction = "horizontal"

        else:

            width = min(
                walkway_width_mm,
                egress_zone.width_mm,
            )

            depth = egress_zone.depth_mm

            x_mm = egress_zone.x_mm
            y_mm = egress_zone.y_mm

            direction = "vertical"

        (
            x_mm,
            y_mm,
            width,
            depth,
        ) = _clamp_zone(
            x_mm,
            y_mm,
            width,
            depth,
            room,
        )

        zones.append(
            Zone(
                zone_id=(
                    f"{room.room_id}"
                    f"-walkway-{direction}"
                ),
                zone_type="walkway",
                x_mm=x_mm,
                y_mm=y_mm,
                width_mm=width,
                depth_mm=depth,
                priority=0,
            )
        )

    return zones


def protected_zones(
    zones: Dict[str, List[Zone]],
) -> List[Zone]:

    protected = []

    protected.extend(
        zones.get("windows", [])
    )

    protected.extend(
        zones.get("doors", [])
    )

    protected.extend(
        zones.get("egress", [])
    )

    protected.extend(
        zones.get("walkway", [])
    )

    return protected


def build_zones(room) -> Dict[str, List[Zone]]:

    usable = [
        create_usable_zone(room)
    ]

    perimeter = create_perimeter_zones(
        room
    )

    open_zones = [
        create_open_zone(room)
    ]

    windows = create_window_zones(
        room
    )

    doors = create_door_zones(
        room
    )

    egress = create_egress_zones(
        room
    )

    walkway = create_walkway_zones(
        room,
        egress,
    )

    zones = {
        "usable": usable,
        "perimeter": perimeter,
        "open": open_zones,
        "windows": windows,
        "doors": doors,
        "egress": egress,
        "walkway": walkway,
    }

    zones["protected"] = protected_zones(
        zones
    )

    return zones