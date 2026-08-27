from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Product:
    sku: str
    family: str
    name: str
    width_mm: int
    depth_mm: int
    height_mm: int
    unit_list_price_inr: int
    labour_minutes: int
    lead_time_days: int
    compatible_finishes: List[str]


@dataclass
class Finish:
    finish_id: str
    name: str
    uplift_bps: int
    compatible_families: List[str]


@dataclass
class Rule:
    rule_id: str
    kind: str
    severity: str
    details: Dict[str, Any]


@dataclass
class Room:
    room_id: str
    name: str
    boundary_mm: List[List[int]]
    doors: List[Dict[str, Any]]
    windows: List[Dict[str, Any]]
    egress: Dict[str, Any]
    capacity: int


@dataclass
class Brief:
    room_id: str
    text: str