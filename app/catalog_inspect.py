import json
from collections import Counter
from pathlib import Path

from app.config import CATALOG_FILE, FINISHES_FILE, HISTORICAL_JOBS_FILE
from app.loader import load_json


def main():
    catalog = load_json(CATALOG_FILE)
    finishes = load_json(FINISHES_FILE)
    historical_jobs = load_json(HISTORICAL_JOBS_FILE)

    print("\n================================")
    print(" RuleBound Catalog Inspection")
    print("================================\n")

    # ---------------------------------------------------------
    # Basic counts
    # ---------------------------------------------------------

    print("CATALOG SUMMARY")
    print("----------------")
    print(f"Products : {len(catalog)}")
    print(f"Finishes : {len(finishes)}")
    print(f"Historical jobs : {len(historical_jobs)}")
    print()

    # ---------------------------------------------------------
    # Product families
    # ---------------------------------------------------------

    family_counts = Counter(
        item["family"]
        for item in catalog
    )

    print("PRODUCT FAMILIES")
    print("----------------")

    for family, count in sorted(
        family_counts.items()
    ):
        print(f"{family:20} {count}")

    print()

    # ---------------------------------------------------------
    # Price ranges
    # ---------------------------------------------------------

    prices = [
        item["list_price_inr"]
        for item in catalog
    ]

    print("PRICE RANGE")
    print("-----------")
    print(f"Minimum : ₹{min(prices):,.0f}")
    print(f"Maximum : ₹{max(prices):,.0f}")
    print(f"Average : ₹{sum(prices) / len(prices):,.0f}")
    print()

    # ---------------------------------------------------------
    # Labour ranges
    # ---------------------------------------------------------

    labour = [
        item["labour_minutes"]
        for item in catalog
    ]

    print("LABOUR RANGE")
    print("------------")
    print(f"Minimum : {min(labour)} minutes")
    print(f"Maximum : {max(labour)} minutes")
    print(f"Average : {sum(labour) / len(labour):.1f} minutes")
    print()

    # ---------------------------------------------------------
    # Lead time
    # ---------------------------------------------------------

    lead_times = [
        item["lead_time_days"]
        for item in catalog
    ]

    print("LEAD TIME RANGE")
    print("---------------")
    print(f"Minimum : {min(lead_times)} days")
    print(f"Maximum : {max(lead_times)} days")
    print(f"Average : {sum(lead_times) / len(lead_times):.1f} days")
    print()

    # ---------------------------------------------------------
    # Dimensions by family
    # ---------------------------------------------------------

    print("DIMENSION RANGES BY FAMILY")
    print("--------------------------")

    for family in sorted(family_counts):

        products = [
            item
            for item in catalog
            if item["family"] == family
        ]

        widths = [
            item["dimensions_mm"]["width"]
            for item in products
        ]

        depths = [
            item["dimensions_mm"]["depth"]
            for item in products
        ]

        heights = [
            item["dimensions_mm"]["height"]
            for item in products
        ]

        print(f"\n{family}")

        print(
            f"  Width  : {min(widths)} - {max(widths)} mm"
        )

        print(
            f"  Depth  : {min(depths)} - {max(depths)} mm"
        )

        print(
            f"  Height : {min(heights)} - {max(heights)} mm"
        )

    print()

    # ---------------------------------------------------------
    # Finish compatibility
    # ---------------------------------------------------------

    finish_usage = Counter()

    for item in catalog:
        for finish_id in item.get(
            "compatible_finish_ids",
            [],
        ):
            finish_usage[finish_id] += 1

    print("FINISH COMPATIBILITY")
    print("--------------------")

    for finish_id, count in sorted(
        finish_usage.items()
    ):
        print(
            f"{finish_id:5} → "
            f"{count} products"
        )

    print()

    # ---------------------------------------------------------
    # Historical SKU usage
    # ---------------------------------------------------------

    historical_skus = Counter()

    for job in historical_jobs:

        for line_item in job.get(
            "line_items",
            [],
        ):
            historical_skus[
                line_item["sku"]
            ] += line_item.get(
                "quantity",
                0,
            )

    print("HISTORICAL SKU USAGE")
    print("--------------------")

    for sku, quantity in historical_skus.most_common():
        print(
            f"{sku:15} → "
            f"{quantity} units"
        )

    print()

    # ---------------------------------------------------------
    # Sample products by family
    # ---------------------------------------------------------

    print("SAMPLE PRODUCTS")
    print("---------------")

    for family in sorted(family_counts):

        products = [
            item
            for item in catalog
            if item["family"] == family
        ]

        print(f"\n[{family}]")

        for item in products[:3]:

            dimensions = item["dimensions_mm"]

            print(
                f"  {item['sku']} | "
                f"{item['name']} | "
                f"{dimensions['width']}x"
                f"{dimensions['depth']}x"
                f"{dimensions['height']} mm | "
                f"₹{item['list_price_inr']:,}"
            )

    print("\n================================")
    print(" Inspection Complete")
    print("================================")


if __name__ == "__main__":
    main()