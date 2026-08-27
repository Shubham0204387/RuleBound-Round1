from app.loader import load_all_data


def check_products(products, finish_ids):
    errors = []

    if len(products) != 120:
        errors.append(f"Expected 120 products, found {len(products)}")

    if len(products) != len(set(products.keys())):
        errors.append("Duplicate product SKU detected")

    for sku, product in products.items():
        if not sku:
            errors.append("Product with empty SKU found")

        if product.width_mm <= 0:
            errors.append(f"{sku}: width must be positive")

        if product.depth_mm <= 0:
            errors.append(f"{sku}: depth must be positive")

        if product.height_mm <= 0:
            errors.append(f"{sku}: height must be positive")

        if product.unit_list_price_inr < 0:
            errors.append(f"{sku}: price cannot be negative")

        if product.labour_minutes < 0:
            errors.append(f"{sku}: labour minutes cannot be negative")

        if product.lead_time_days < 0:
            errors.append(f"{sku}: lead time cannot be negative")

        for finish_id in product.compatible_finishes:
            if finish_id not in finish_ids:
                errors.append(
                    f"{sku}: references unknown finish {finish_id}"
                )

    return errors


def check_finishes(finishes):
    errors = []

    if len(finishes) != 18:
        errors.append(f"Expected 18 finishes, found {len(finishes)}")

    if len(finishes) != len(set(finishes.keys())):
        errors.append("Duplicate finish ID detected")

    for finish_id, finish in finishes.items():
        if not finish_id:
            errors.append("Finish with empty ID found")

        if finish.uplift_bps < 0:
            errors.append(
                f"{finish_id}: uplift cannot be negative"
            )

    return errors


def check_rules(rules):
    errors = []

    if len(rules) != 14:
        errors.append(f"Expected 14 rules, found {len(rules)}")

    if len(rules) != len(set(rules.keys())):
        errors.append("Duplicate rule ID detected")

    for rule_id, rule in rules.items():
        if not rule_id:
            errors.append("Rule with empty ID found")

        if not rule.kind:
            errors.append(f"{rule_id}: missing rule kind")

        if not rule.severity:
            errors.append(f"{rule_id}: missing severity")

    return errors


def check_rooms(rooms):
    errors = []

    if len(rooms) != 5:
        errors.append(f"Expected 5 rooms, found {len(rooms)}")

    if len(rooms) != len(set(rooms.keys())):
        errors.append("Duplicate room ID detected")

    for room_id, room in rooms.items():

        if not room.boundary_mm:
            errors.append(f"{room_id}: missing boundary")

        if len(room.boundary_mm) < 3:
            errors.append(
                f"{room_id}: boundary must have at least 3 points"
            )

        if not room.doors:
            errors.append(f"{room_id}: no doors defined")

        if not room.egress:
            errors.append(f"{room_id}: missing egress")

        if room.capacity <= 0:
            errors.append(
                f"{room_id}: capacity must be positive"
            )

        for point in room.boundary_mm:
            if not isinstance(point, list) or len(point) != 2:
                errors.append(
                    f"{room_id}: invalid boundary point {point}"
                )

    return errors


def check_briefs(briefs, rooms):
    errors = []

    if len(briefs) != len(rooms):
        errors.append(
            f"Expected one brief per room: "
            f"{len(rooms)} rooms, {len(briefs)} briefs"
        )

    for room_id in rooms:
        if room_id not in briefs:
            errors.append(
                f"{room_id}: missing customer brief"
            )

    for room_id, brief in briefs.items():
        if not brief.text.strip():
            errors.append(
                f"{room_id}: brief is empty"
            )

    return errors


def run_checks():
    print("\n================================")
    print(" RuleBound Application Data Check")
    print("================================\n")

    data = load_all_data()

    products = data["catalog"]
    finishes = data["finishes"]
    rules = data["rules"]
    rooms = data["rooms"]
    briefs = data["briefs"]

    all_errors = []

    checks = [
        ("Products", check_products(
            products,
            set(finishes.keys())
        )),
        ("Finishes", check_finishes(finishes)),
        ("Rules", check_rules(rules)),
        ("Rooms", check_rooms(rooms)),
        ("Briefs", check_briefs(briefs, rooms)),
    ]

    for name, errors in checks:
        if errors:
            print(f"no {name}")
            for error in errors:
                print(f"   - {error}")
            all_errors.extend(errors)
        else:
            print(f"yes {name}")

    print()

    if all_errors:
        print(
            f"DATA CHECK FAILED: "
            f"{len(all_errors)} issue(s) found."
        )
        return False

    print(" DATA CHECK PASSED!")
    print("The RuleBound dataset is ready for our application.")
    return True


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)