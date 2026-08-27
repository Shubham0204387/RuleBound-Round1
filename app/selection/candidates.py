from app.resolution.models import (
    ResolvedFurnitureRequirement,
)

from app.selection.models import (
    CandidateCheck,
    CandidateSet,
    ProductCandidate,
)


def build_historical_usage(historical_jobs):
    usage = {}

    for job in historical_jobs:

        for line_item in job.get(
            "line_items",
            [],
        ):

            sku = line_item.get("sku")
            quantity = line_item.get(
                "quantity",
                0,
            )

            if sku is None:
                continue

            usage[sku] = (
                usage.get(sku, 0)
                + quantity
            )

    return usage


def build_candidates(
    room_id: str,
    requirement: ResolvedFurnitureRequirement,
    catalog,
    historical_jobs=None,
    requested_finish_ids=None,
):
    historical_jobs = historical_jobs or []

    requested_finish_ids = (
        requested_finish_ids or []
    )

    historical_usage = build_historical_usage(
        historical_jobs
    )

    candidates = []
    rejected = []

    for product in catalog.values():

        checks = []

        family_match = (
            product.family == requirement.family
        )

        checks.append(
            CandidateCheck(
                name="family",
                passed=family_match,
                reason=(
                    "Product family matches requirement."
                    if family_match
                    else (
                        f"Product family "
                        f"'{product.family}' does not "
                        f"match required family "
                        f"'{requirement.family}'."
                    )
                ),
            )
        )

        if not family_match:

            rejected.append(
                {
                    "sku": product.sku,
                    "reason": "family_mismatch",
                }
            )

            continue

        finish_match = True

        if requested_finish_ids:

            finish_match = any(
                finish_id
                in product.compatible_finishes
                for finish_id in requested_finish_ids
            )

        checks.append(
            CandidateCheck(
                name="finish_compatibility",
                passed=finish_match,
                reason=(
                    "Product supports at least one "
                    "requested finish."
                    if finish_match
                    else (
                        "Product does not support any "
                        "requested finish."
                    )
                ),
            )
        )

        if not finish_match:

            rejected.append(
                {
                    "sku": product.sku,
                    "reason": "finish_incompatible",
                }
            )

            continue

        valid_price = (
            product.unit_list_price_inr >= 0
        )

        valid_labour = (
            product.labour_minutes >= 0
        )

        valid_lead_time = True

        if hasattr(
            product,
            "lead_time_days",
        ):
            valid_lead_time = (
                product.lead_time_days >= 0
            )

        catalog_data_valid = (
            valid_price
            and valid_labour
            and valid_lead_time
        )

        checks.append(
            CandidateCheck(
                name="catalog_data",
                passed=catalog_data_valid,
                reason=(
                    "Required catalog values are valid."
                    if catalog_data_valid
                    else (
                        "Product contains invalid "
                        "catalog values."
                    )
                ),
            )
        )

        if not catalog_data_valid:

            rejected.append(
                {
                    "sku": product.sku,
                    "reason": "invalid_catalog_data",
                }
            )

            continue

        evidence = []

        if requirement.quantity_status == "explicit":

            evidence.append(
                "Quantity comes directly from the "
                "customer requirement."
            )

        elif requirement.quantity_status == "inferred_high":

            evidence.append(
                "Quantity was resolved using a "
                "high-confidence inference."
            )

        elif requirement.quantity_status == "inferred_medium":

            evidence.append(
                "Quantity was resolved using a "
                "medium-confidence inference."
            )

        elif requirement.quantity_status == "unresolved":

            evidence.append(
                "Required quantity remains unresolved."
            )

        if requirement.attributes:

            evidence.append(
                "Catalog does not directly encode "
                "semantic attributes: "
                + ", ".join(
                    requirement.attributes
                )
            )

        historical_quantity = historical_usage.get(
            product.sku,
            0,
        )

        if historical_quantity > 0:

            evidence.append(
                f"Historical usage: "
                f"{historical_quantity} units."
            )

        else:

            evidence.append(
                "No historical usage recorded."
            )

        candidate = ProductCandidate(
            sku=product.sku,
            family=product.family,
            name=product.name,
            quantity=requirement.quantity,
            list_price_inr=product.unit_list_price_inr,
            labour_minutes=product.labour_minutes,
            lead_time_days=getattr(
                product,
                "lead_time_days",
                0,
            ),
            compatible_finish_ids=list(
                product.compatible_finishes
            ),
            historical_quantity=historical_quantity,
            checks=checks,
            evidence=evidence,
        )

        candidates.append(candidate)

    return CandidateSet(
        room_id=room_id,
        family=requirement.family,
        quantity=requirement.quantity,
        quantity_status=requirement.quantity_status,
        candidates=candidates,
        rejected=rejected,
    )