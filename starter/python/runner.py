from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection import select_product
from app.layout.assembler import assemble_layout
from app.layout.validator import validate_layout
from app.layout.repair import repair_layout
from app.layout.models import Violation


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def requested_finish_ids_from_preferences(requirements):
    """
    Convert recognized semantic finish preferences into deterministic
    catalog finish IDs.
    """
    preference_to_finish = {
        "natural_oak": "F03",
        "graphite": "F02",
    }

    finish_ids = []

    for preference in getattr(
        requirements,
        "preferences",
        [],
    ):
        if getattr(preference, "category", None) != "finish":
            continue

        finish_id = preference_to_finish.get(
            getattr(preference, "value", None)
        )

        if finish_id and finish_id not in finish_ids:
            finish_ids.append(finish_id)

    return finish_ids


def resolve_room_finish(requirements, selected_products, finishes):
    """
    Resolve one deterministic room-wide finish.

    Explicit supported finish preferences take priority. A preferred finish
    is usable only when every selected product family supports it. If no
    preferred
    finish covers all selected families, choose the lowest-uplift universal
    finish deterministically.
    """
    preference_to_finish = {
        "natural_oak": "F03",
        "graphite": "F02",
    }

    preferred_finish_ids = []

    for preference in getattr(requirements, "preferences", []):
        finish_id = preference_to_finish.get(
            getattr(preference, "value", None)
        )

        if finish_id and finish_id not in preferred_finish_ids:
            preferred_finish_ids.append(finish_id)

    selected_families = sorted(
        family
        for family, product in selected_products.items()
        if product is not None
    )

    for finish_id in preferred_finish_ids:
        finish = finishes.get(finish_id)

        if finish is None:
            continue

        if all(
            family in finish.compatible_families
            for family in selected_families
        ):
            return finish_id

    universal = [
        finish
        for finish in finishes.values()
        if all(
            family in finish.compatible_families
            for family in selected_families
        )
    ]

    if not universal:
        return None

    return min(
        universal,
        key=lambda finish: (
            finish.uplift_bps,
            finish.finish_id,
        ),
    ).finish_id


def build_quote(
    room_id,
    layout,
    catalog,
    finishes,
    selected_products,
):
    """
    Deterministic pricing based only on committed placements.

    No timestamps, randomness, network calls or model calls.

    Quote lines are aggregated deterministically by SKU + finish.

    Pricing pipeline:

        base amount
        + finish uplift
        - quantity discount
        = net goods

        total labour minutes
        -> labour band
        -> labour amount

        net goods
        -> freight band
        -> freight amount

        goods + labour + freight
        = grand total

    RB-PRC-013:
        Any committed placement that cannot be priced must block
        the quote rather than being silently omitted.
    """

    grouped = {}
    pricing_blockers = []

    # ============================================================
    # 1. Aggregate committed placements
    # ============================================================

    for placement in sorted(
        layout.placements,
        key=lambda item: (
            item.sku,
            item.finish_id,
            item.placement_id,
        ),
    ):
        product = catalog.get(placement.sku)

        if product is None:
            pricing_blockers.append(
                {
                    "placement_id": placement.placement_id,
                    "sku": placement.sku,
                    "finish_id": placement.finish_id,
                    "reason": (
                        f"No catalog price exists for SKU "
                        f"'{placement.sku}'."
                    ),
                }
            )
            continue

        key = (
            placement.sku,
            placement.finish_id,
        )

        if key not in grouped:
            grouped[key] = {
                "sku": placement.sku,
                "finish_id": placement.finish_id,
                "quantity": 0,
                "placement_ids": [],
            }

        grouped[key]["quantity"] += 1
        grouped[key]["placement_ids"].append(
            placement.placement_id
        )

    # ============================================================
    # 2. Build deterministic quote lines
    # ============================================================

    lines = []

    for group in sorted(
        grouped.values(),
        key=lambda item: (
            item["sku"],
            item["finish_id"],
        ),
    ):
        product = catalog.get(group["sku"])

        if product is None:
            # Already recorded as an RB-PRC-013 blocker above.
            continue

        quantity = group["quantity"]
        unit_price = product.unit_list_price_inr

        # --------------------------------------------------------
        # Base amount
        # --------------------------------------------------------

        base_amount = unit_price * quantity

        # --------------------------------------------------------
        # Finish uplift - RB-PRC-010
        # --------------------------------------------------------

        finish = finishes.get(group["finish_id"])

        if finish is None:
            pricing_blockers.append(
                {
                    "placement_ids": group["placement_ids"],
                    "sku": group["sku"],
                    "finish_id": group["finish_id"],
                    "reason": (
                        f"Finish '{group['finish_id']}' is not "
                        f"priced or does not exist."
                    ),
                }
            )
            continue

        # --------------------------------------------------------
        # Finish compatibility - RB-PRC-013
        # --------------------------------------------------------

        if product.family not in finish.compatible_families:
            pricing_blockers.append(
                {
                    "placement_ids": group["placement_ids"],
                    "sku": group["sku"],
                    "finish_id": group["finish_id"],
                    "reason": (
                        f"Finish '{group['finish_id']}' is incompatible "
                        f"with product family '{product.family}'."
                    ),
                }
            )
            continue

        uplift_bps = finish.uplift_bps

        # Integer round-half-up:
        #
        # round_half_up(
        #     base_amount * uplift_bps / 10000
        # )
        #
        finish_uplift = (
            base_amount * uplift_bps + 5000
        ) // 10000

        # --------------------------------------------------------
        # Quantity discount - RB-PRC-009
        # --------------------------------------------------------

        if quantity >= 20:
            discount_bps = 1000
        elif quantity >= 10:
            discount_bps = 700
        elif quantity >= 5:
            discount_bps = 300
        else:
            discount_bps = 0

        # Integer round-half-up:
        #
        # round_half_up(
        #     base_amount * discount_bps / 10000
        # )
        #
        quantity_discount = (
            base_amount * discount_bps + 5000
        ) // 10000

        # --------------------------------------------------------
        # Net goods
        # --------------------------------------------------------

        net_goods = (
            base_amount
            + finish_uplift
            - quantity_discount
        )

        lines.append(
            {
                "line_id": f"LINE-{len(lines) + 1:04d}",
                "sku": group["sku"],
                "finish_id": group["finish_id"],
                "quantity": quantity,
                "unit_list_price_inr": unit_price,
                "base_amount_inr": base_amount,
                "finish_uplift_inr": finish_uplift,
                "quantity_discount_inr": quantity_discount,
                "net_goods_inr": net_goods,
                "trace": [
                    {
                        "rule_id": "CATALOG",
                        "inputs": {
                            "unit_price": unit_price,
                            "quantity": quantity,
                        },
                        "amount_inr": base_amount,
                    },
                    {
                        "rule_id": "RB-PRC-010",
                        "inputs": {
                            "uplift_bps": uplift_bps,
                            "base_amount_inr": base_amount,
                        },
                        "amount_inr": finish_uplift,
                    },
                    {
                        "rule_id": "RB-PRC-009",
                        "inputs": {
                            "discount_bps": discount_bps,
                            "base_amount_inr": base_amount,
                        },
                        "amount_inr": -quantity_discount,
                    },
                ],
            }
        )

    # ============================================================
    # 3. Labour pricing - RB-PRC-011
    # ============================================================

    total_labour_minutes = 0

    for line in lines:
        product = catalog[line["sku"]]

        total_labour_minutes += (
            product.labour_minutes
            * line["quantity"]
        )

    # Labour band:
    #
    # <= 240 minutes  -> ₹900/hour
    # 241-480 minutes -> ₹800/hour
    # > 480 minutes   -> ₹750/hour
    #
    if total_labour_minutes <= 240:
        labour_rate = 900
    elif total_labour_minutes <= 480:
        labour_rate = 800
    else:
        labour_rate = 750

    # Integer round-half-up:
    #
    # round_half_up(
    #     total_labour_minutes * labour_rate / 60
    # )
    #
    labour_inr = (
        total_labour_minutes * labour_rate + 30
    ) // 60

    # ============================================================
    # 4. Goods total
    # ============================================================

    goods_total = sum(
        line["net_goods_inr"]
        for line in lines
    )

    # ============================================================
    # 5. Freight pricing - RB-PRC-012
    # ============================================================

    if goods_total <= 100000:
        freight_band = "UP_TO_100K"
        freight_rate_bps = None
        freight_inr = 5000

    elif goods_total <= 250000:
        freight_band = "100K_TO_250K"
        freight_rate_bps = None
        freight_inr = 9000

    else:
        freight_band = "ABOVE_250K"
        freight_rate_bps = 400

        # Integer round-half-up:
        #
        # round_half_up(
        #     goods_total * 400 / 10000
        # )
        #
        freight_inr = (
            goods_total * freight_rate_bps + 5000
        ) // 10000

    # ============================================================
    # 6. Grand total
    # ============================================================

    grand_total = (
        goods_total
        + labour_inr
        + freight_inr
    )

    # ============================================================
    # 7. Summary trace
    # ============================================================

    summary_trace = [
        {
            "rule_id": "RB-PRC-011",
            "inputs": {
                "total_labour_minutes": total_labour_minutes,
                "labour_rate_inr_per_hour": labour_rate,
            },
            "amount_inr": labour_inr,
        },
        {
            "rule_id": "RB-PRC-012",
            "inputs": {
                "goods_after_adjustments_inr": goods_total,
                "freight_band": freight_band,
                "freight_rate_bps": freight_rate_bps,
            },
            "amount_inr": freight_inr,
        },
    ]

    # ============================================================
    # 8. RB-PRC-013 blocking trace
    # ============================================================

    if pricing_blockers:
        summary_trace.append(
            {
                "rule_id": "RB-PRC-013",
                "inputs": {
                    "blocking_line_count": len(
                        pricing_blockers
                    ),
                },
                "amount_inr": 0,
            }
        )

    # ============================================================
    # 9. Valid layout + no pricing blockers
    # ============================================================

    if layout.status == "valid" and not pricing_blockers:
        return {
            "quote_id": f"QUOTE-{room_id}",
            "room_id": room_id,
            "currency": "INR",
            "lines": lines,
            "summary": {
                "goods_after_adjustments_inr": goods_total,
                "labour_minutes": total_labour_minutes,
                "labour_rate_inr_per_hour": labour_rate,
                "labour_inr": labour_inr,
                "freight_inr": freight_inr,
                "grand_total_inr": grand_total,
            },
            "summary_trace": summary_trace,
            "status": "priced",
        }

    # ============================================================
    # 10. Blocked quote
    # ============================================================

    blocking_reasons = [
        violation.message
        for violation in layout.violations
    ]

    for blocker in pricing_blockers:
        blocking_reasons.append(
            blocker["reason"]
        )

    if not blocking_reasons:
        blocking_reasons = [
            "Layout is not valid."
        ]

    return {
        "quote_id": f"QUOTE-{room_id}",
        "room_id": room_id,
        "currency": "INR",
        "lines": lines,
        "summary": {
            "goods_after_adjustments_inr": goods_total,
            "labour_minutes": total_labour_minutes,
            "labour_rate_inr_per_hour": labour_rate,
            "labour_inr": labour_inr,
            "freight_inr": freight_inr,
            "grand_total_inr": grand_total,
        },
        "summary_trace": summary_trace,
        "status": "blocked",
        "blocking_reasons": blocking_reasons,
    }


def process_room(
    room,
    brief,
    data,
):
    room_id = room.room_id

    # ============================================================
    # 1. Extract customer requirements
    # ============================================================

    requirements = extract_requirements(
        room_id,
        brief.text,
    )

    # ============================================================
    # 2. Resolve requirements
    # ============================================================

    resolved = resolve_requirements(
        requirements
    )

    # ============================================================
    # 3. Select products
    # ============================================================

    selected_products = {}

    for requirement in resolved.furniture:

        requested_finish_ids = (
            requested_finish_ids_from_preferences(
                resolved
            )
        )

        result = select_product(
            room_id=room_id,
            requirement=requirement,
            catalog=data["catalog"],
            historical_jobs=data["historical_jobs"],
            requested_finish_ids=requested_finish_ids,
        )

        if result.selected is None:
            continue

        sku = result.selected.candidate.sku

        selected_products[
            requirement.family
        ] = data["catalog"][sku]

    # ============================================================
    # 4. Assemble layout
    # ============================================================

    room_finish_id = resolve_room_finish(
        requirements=resolved,
        selected_products=selected_products,
        finishes=data["finishes"],
    )

    if room_finish_id is None:
        raise RuntimeError(
            f"No compatible finish exists for room '{room_id}'."
        )

    assembly = assemble_layout(
        room=room,
        selected_products=selected_products,
        requirements=resolved,
        catalog=data["catalog"],
        finish_id=room_finish_id,
        step_mm=300,
        candidates_per_item=30,
    )

    layout = assembly.layout

    # ============================================================
    # 5. Validate and repair generated layout
    # ============================================================

    layout = validate_layout(
        layout,
        room,
        data["catalog"],
    )

    layout, escalation = repair_layout(
        layout=layout,
        validate=validate_layout,
        room=room,
        catalog=data["catalog"],
    )

    layout.escalation = escalation

    # ============================================================
    # 6. Handle unresolved requirements
    # ============================================================

    if assembly.unresolved_families:
        layout.status = "unsatisfiable"

        resolved_by_family = {
            item.family: item
            for item in resolved.furniture
        }

        for family in assembly.unresolved_families:

            resolved_item = resolved_by_family.get(
                family
            )

            if (
                resolved_item is not None
                and resolved_item.quantity_status == "unresolved"
                and resolved_item.evidence
            ):
                reason = (
                    resolved_item.evidence[-1].reason
                )
            else:
                reason = (
                    f"Not all required '{family}' items could be "
                    f"placed within the available room geometry "
                    f"while satisfying spatial constraints."
                )

            layout.violations.append(
                Violation(
                    violation_id=(
                        f"V-UNRESOLVED-{family.upper()}"
                    ),
                    rule_id="RB-REQ-001",
                    message=reason,
                    affected_placement_ids=[],
                )
            )

    # ============================================================
    # 7. Deterministic quote
    # ============================================================

    quote = build_quote(
        room_id=room_id,
        layout=layout,
        catalog=data["catalog"],
        finishes=data["finishes"],
        selected_products=selected_products,
    )

    return layout, quote


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    # NOTE:
    # The current application engine loads its canonical
    # RuleBound data through app.loader.
    #
    # The submission input/output contract is handled here
    # while preserving the already-tested application engine.

    data = load_all_data(
        Path(args.input)
    )

    output_root = Path(
        args.output
    )

    for room_id in sorted(
        data["rooms"].keys()
    ):

        room = data["rooms"][room_id]
        brief = data["briefs"][room_id]

        layout, quote = process_room(
            room=room,
            brief=brief,
            data=data,
        )

        room_output = (
            output_root / room_id
        )

        write_json(
            room_output / "layout.json",
            layout.to_dict(),
        )

        write_json(
            room_output / "quote.json",
            quote,
        )

    print(
        f"Generated deterministic output for "
        f"{len(data['rooms'])} rooms."
    )


if __name__ == "__main__":
    main()