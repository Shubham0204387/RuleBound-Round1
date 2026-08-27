import sys
from app.loader import load_all_data
from app.layout.zones import build_zones
from app.layout.placement import placement_overlaps, placement_inside_room
from app.layout.candidates import (
    _has_wall_offset,
    _clear_of_protected_zones,
    _chair_position_candidates,
    find_chair_candidates_for_desk,
    generate_candidates,
    _minimum_axis_clearance,
    DESK_CHAIR_CLEARANCE_MM,
    get_product_footprint,
    zone_contains_footprint
)
from app.layout.models import Placement
from app.layout.assembler import _chair_is_valid_for_paired_desk, _desk_is_valid, _build_zones

data = load_all_data()
room = data["rooms"]["ROOM-01"]
catalog = data["catalog"]

desk_product = catalog["NW-DES-009"]
chair_product = catalog["NW-CHA-006"]
collab_product = catalog["NW-COL-002"]
storage_product = catalog["NW-STO-018"]
zones = _build_zones(room)

print("=== CHAIR CANDIDATES FOR DESK 1 (x=600, y=1200) ===")
desk_placement = Placement("test-desk", desk_product.sku, "F1", 600, 1200, 0)
raw_chairs = _chair_position_candidates(desk_placement, chair_product, catalog)
for i, c in enumerate(raw_chairs):
    print(f"Raw candidate {i}: x={c[0]}, y={c[1]}")

def test_finer_chairs(step):
    print(f"\nTesting chair generation with sliding offset step {step}mm:")
    desk_fp = get_product_footprint(desk_placement, catalog)
    chair_w = chair_product.width_mm
    chair_d = chair_product.depth_mm
    clearance = DESK_CHAIR_CLEARANCE_MM
    
    valid_chairs = []
    
    x_right = desk_fp.x_mm + desk_fp.width_mm + clearance
    for y in range(int(desk_fp.y_mm - chair_d), int(desk_fp.y_mm + desk_fp.depth_mm + chair_d), step):
        p = Placement("c", chair_product.sku, "F1", x_right, y, 0)
        if _chair_is_valid_for_paired_desk(p, desk_placement, [], catalog):
            if placement_inside_room(p, room, catalog) and _clear_of_protected_zones(p, zones, catalog):
                valid_chairs.append((x_right, y))
    print(f"Right edge valid chairs: {len(valid_chairs)}")

test_finer_chairs(300)
test_finer_chairs(150)
test_finer_chairs(100)
test_finer_chairs(10)

print("\n=== EXHAUSTIVE SEARCH FOR 6 DESKS (with 2 chairs each) ===")
desk_candidates = generate_candidates(room, desk_product, "desk", "F1", zones, catalog, [], step_mm=300, max_candidates=1000)
print(f"Generated {len(desk_candidates)} valid initial desk candidates.")

def solve():
    placements = []
    
    def backtrack(desk_idx):
        if desk_idx == 6:
            return True
            
        for cand in desk_candidates:
            d_place = cand.placement
            d_place.placement_id = f"D{desk_idx}"
            if not _desk_is_valid(d_place, [p for p in placements if p.family=="desk"], placements, catalog):
                continue
                
            chairs = find_chair_candidates_for_desk(room=room, desk=d_place, chair_product=chair_product, finish_id="F1", zones=zones, catalog=catalog, existing_placements=placements)
            if len(chairs) < 2:
                continue
                
            placements.append(d_place)
            placements.append(chairs[0].placement)
            placements.append(chairs[1].placement)
            
            if backtrack(desk_idx + 1):
                return True
                
            placements.pop()
            placements.pop()
            placements.pop()
            
        return False

    if backtrack(0):
        print("FOUND COMPLETE 6-DESK LAYOUT with standard chairs!")
        for p in placements:
            print(f"{p.family}: x={p.x_mm}, y={p.y_mm}")
        return True
    else:
        print("COULD NOT FIND 6-DESK LAYOUT with standard chairs.")
        return False

solve()
