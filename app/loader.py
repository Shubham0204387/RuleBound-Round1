import json
from pathlib import Path
from typing import Dict, Any

from app.config import DATA_DIR

from app.models import Product, Finish, Rule, Room, Brief


def load_json(file_path: Path) -> Any:
    """Load and return JSON data from a file."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_catalog(data_dir: Path = DATA_DIR) -> Dict[str, Product]:
    """
    Load all products from catalog.json.

    The RuleBound catalog stores dimensions inside
    dimensions_mm and prices inside list_price_inr.
    """

    raw_data = load_json(data_dir / "catalog.json")

    products: Dict[str, Product] = {}

    for item in raw_data:
        dimensions = item["dimensions_mm"]

        product = Product(
            sku=item["sku"],
            family=item["family"],
            name=item["name"],
            width_mm=dimensions["width"],
            depth_mm=dimensions["depth"],
            height_mm=dimensions["height"],
            unit_list_price_inr=item["list_price_inr"],
            labour_minutes=item["labour_minutes"],
            lead_time_days=item["lead_time_days"],
            compatible_finishes=item.get("compatible_finish_ids", []),
        )

        products[product.sku] = product

    return products


def load_finishes(data_dir: Path = DATA_DIR) -> Dict[str, Finish]:
    """
    Load all finishes from finishes.json.
    """

    raw_data = load_json(data_dir / "finishes.json")

    finishes: Dict[str, Finish] = {}

    for item in raw_data:
        finish = Finish(
            finish_id=item["finish_id"],
            name=item["name"],
            uplift_bps=item["uplift_bps"],
            compatible_families=item.get("compatible_families", []),
        )

        finishes[finish.finish_id] = finish

    return finishes


def load_rules(data_dir: Path = DATA_DIR) -> Dict[str, Rule]:
    """
    Load all rules from rules.json.
    """

    raw_data = load_json(data_dir / "rules.json")

    rules: Dict[str, Rule] = {}

    for item in raw_data["rules"]:
        rule = Rule(
            rule_id=item["rule_id"],
            kind=item["kind"],
            severity=item["severity"],
            details={
                key: value
                for key, value in item.items()
                if key not in {"rule_id", "kind", "severity"}
            },
        )

        rules[rule.rule_id] = rule

    return rules


def load_rooms(data_dir: Path = DATA_DIR) -> Dict[str, Room]:
    """
    Load all room JSON files.

    Room geometry is represented by boundary_mm rather than
    simple width/depth fields because some rooms may be
    non-rectangular, such as the L-shaped ROOM-03.
    """

    rooms: Dict[str, Room] = {}

    for file_path in sorted((data_dir / "rooms").glob("*.json")):
        raw_data = load_json(file_path)

        room = Room(
            room_id=raw_data["room_id"],
            name=raw_data["name"],
            boundary_mm=raw_data["boundary_mm"],
            doors=raw_data["doors"],
            windows=raw_data["windows"],
            egress=raw_data["egress"],
            capacity=raw_data["capacity"],
        )

        rooms[room.room_id] = room

    return rooms


def load_briefs(data_dir: Path = DATA_DIR) -> Dict[str, Brief]:
    """
    Load all customer briefs from the briefs directory.

    Each brief filename corresponds to a room ID.
    Example:
        ROOM-01.txt -> ROOM-01
    """

    briefs: Dict[str, Brief] = {}

    for file_path in sorted((data_dir / "briefs").glob("*")):
        if not file_path.is_file():
            continue

        room_id = file_path.stem

        text = file_path.read_text(encoding="utf-8").strip()

        briefs[room_id] = Brief(
            room_id=room_id,
            text=text,
        )

    return briefs


def load_historical_jobs(data_dir: Path = DATA_DIR):
    """
    Load historical jobs.

    Historical jobs are kept as raw dictionaries for now because
    they are reference data rather than active application entities.
    """

    return load_json(data_dir / "historical_jobs.json")


def load_all_data(data_dir: Path = DATA_DIR) -> Dict[str, Any]:
    """
    Load the complete RuleBound dataset.
    """

    return {
        "catalog": load_catalog(data_dir),
        "finishes": load_finishes(data_dir),
        "rules": load_rules(data_dir),
        "rooms": load_rooms(data_dir),
        "briefs": load_briefs(data_dir),
        "historical_jobs": load_historical_jobs(data_dir),
    }