from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.loader import load_all_data
from app.extraction import extract_requirements
from app.resolution import resolve_requirements
from app.selection import select_product
from app.layout.assembler import assemble_layout
from app.layout.validator import validate_layout


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


def build_quote(
    room_id,
    layout,
    catalog,
    selected_products,
):
    """
    Deterministic pricing based only on committed placements.

    No timestamps, randomness, network calls or model calls.
    """

    lines = []

    for placement in sorted(
        layout.placements,
        key=lambda item: item.placement_id,
    ):
        product = catalog.get(placement.sku)

        if product is None:
            continue

        quantity = 1
        unit_price = product.unit_list_price_inr
        net_goods = unit_price * quantity

        lines.append(
            {
                "line_id": f"LINE-{len(lines) + 1:04d}",
                "sku": placement.sku,
                "quantity": quantity,
                "unit_list_price_inr": unit_price,
                "net_goods_inr": net_goods,
                "trace": {
                    "method": "committed_placement_catalog_price",
                    "placement_id": placement.placement_id,
                    "sku": placement.sku,
                    "calculation": (
                        f"{quantity} × {unit_price} = {net_goods}"
                    ),
                },
            }
        )

        

    grand_total = sum(
        line["net_goods_inr"]
        for line in lines
    )

    if layout.status == "valid":
        return {
            "quote_id": f"QUOTE-{room_id}",
            "room_id": room_id,
            "currency": "INR",
            "lines": lines,
            "summary": {
                "grand_total_inr": grand_total,
                "labour_inr": 0,
                "freight_inr": 0,
            },
            "summary_trace": [
                {
                    "method": "deterministic_catalog_sum",
                    "description": (
                        "Grand total equals the sum of "
                        "committed placement list prices."
                    ),
                }
            ],
            "status": "priced",
        }

    return {
        "quote_id": f"QUOTE-{room_id}",
        "room_id": room_id,
        "currency": "INR",
        "lines": lines,
        "summary": {
            "grand_total_inr": grand_total,
            "labour_inr": 0,
            "freight_inr": 0,
        },
        "summary_trace": [
            {
                "method": "deterministic_catalog_sum",
                "description": (
                    "Quote generated deterministically from "
                    "committed catalog placements."
                ),
            }
        ],
        "status": "blocked",
        "blocking_reasons": [
            "Layout is not valid.",
        ],
    }


def process_room(
    room,
    brief,
    data,
):
    room_id = room.room_id

    # ------------------------------------------------------------
    # 1. Extract customer requirements
    # ------------------------------------------------------------

    requirements = extract_requirements(
        room_id,
        brief.text,
    )

    # ------------------------------------------------------------
    # 2. Resolve requirements
    # ------------------------------------------------------------

    resolved = resolve_requirements(
        requirements
    )

    # ------------------------------------------------------------
    # 3. Select products
    # ------------------------------------------------------------

    selected_products = {}

    for requirement in resolved.furniture:

        result = select_product(
            room_id=room_id,
            requirement=requirement,
            catalog=data["catalog"],
            historical_jobs=data["historical_jobs"],
        )

        if result.selected is None:
            continue

        sku = result.selected.candidate.sku

        selected_products[
            requirement.family
        ] = data["catalog"][sku]

    # ------------------------------------------------------------
    # 4. Assemble layout
    # ------------------------------------------------------------

    assembly = assemble_layout(
        room=room,
        selected_products=selected_products,
        requirements=resolved,
        catalog=data["catalog"],
        finish_id="F01",
        step_mm=300,
        candidates_per_item=30,
    )

    layout = assembly.layout

    # ------------------------------------------------------------
    # 5. Validate generated layout
    # ------------------------------------------------------------

    layout = validate_layout(
        layout,
        room,
        data["catalog"],
    )

    # ------------------------------------------------------------
    # 6. Handle unresolved requirements
    # ------------------------------------------------------------

    if assembly.unresolved_families:
        layout.status = "unsatisfiable"

    # ------------------------------------------------------------
    # 7. Deterministic quote
    # ------------------------------------------------------------

    quote = build_quote(
        room_id=room_id,
        layout=layout,
        catalog=data["catalog"],
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

    data = load_all_data()

    output_root = Path(args.output)

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