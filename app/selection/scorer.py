from dataclasses import dataclass
from typing import Dict, List

from app.selection.models import ProductCandidate


WEIGHTS = {
    "price": 0.25,
    "labour": 0.15,
    "lead_time": 0.10,
    "historical": 0.20,
    "finish": 0.30,
}


@dataclass
class ScoreBreakdown:
    price: float
    labour: float
    lead_time: float
    historical: float
    finish: float
    total: float


@dataclass
class ScoredCandidate:
    candidate: ProductCandidate
    breakdown: ScoreBreakdown


def normalize_lower_is_better(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    if maximum == minimum:
        return 1.0

    return (
        maximum - value
    ) / (
        maximum - minimum
    )


def normalize_higher_is_better(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    if maximum == minimum:
        return 1.0

    return (
        value - minimum
    ) / (
        maximum - minimum
    )


def calculate_historical_score(
    candidate: ProductCandidate,
    candidates: List[ProductCandidate],
) -> float:

    maximum = max(
        (
            item.historical_quantity
            for item in candidates
        ),
        default=0,
    )

    if maximum == 0:
        return 0.5

    return (
        candidate.historical_quantity
        / maximum
    )


def calculate_finish_score(
    candidate: ProductCandidate,
    requested_finish_ids=None,
) -> float:

    requested_finish_ids = (
        requested_finish_ids or []
    )

    if not requested_finish_ids:
        return 0.5

    matches = [
        finish_id
        for finish_id in requested_finish_ids
        if finish_id
        in candidate.compatible_finish_ids
    ]

    if matches:
        return 1.0

    return 0.0


def score_candidates(
    candidates: List[ProductCandidate],
    requested_finish_ids=None,
) -> List[ScoredCandidate]:

    if not candidates:
        return []

    requested_finish_ids = (
        requested_finish_ids or []
    )

    prices = [
        candidate.list_price_inr
        for candidate in candidates
    ]

    labours = [
        candidate.labour_minutes
        for candidate in candidates
    ]

    lead_times = [
        candidate.lead_time_days
        for candidate in candidates
    ]

    min_price = min(prices)
    max_price = max(prices)

    min_labour = min(labours)
    max_labour = max(labours)

    min_lead_time = min(lead_times)
    max_lead_time = max(lead_times)

    available_weights = dict(WEIGHTS)

    if not requested_finish_ids:
        available_weights.pop(
            "finish"
        )

    weight_total = sum(
        available_weights.values()
    )

    normalized_weights = {
        key: value / weight_total
        for key, value
        in available_weights.items()
    }

    scored = []

    for candidate in candidates:

        price_score = normalize_lower_is_better(
            candidate.list_price_inr,
            min_price,
            max_price,
        )

        labour_score = normalize_lower_is_better(
            candidate.labour_minutes,
            min_labour,
            max_labour,
        )

        lead_time_score = normalize_lower_is_better(
            candidate.lead_time_days,
            min_lead_time,
            max_lead_time,
        )

        historical_score = (
            calculate_historical_score(
                candidate,
                candidates,
            )
        )

        finish_score = calculate_finish_score(
            candidate,
            requested_finish_ids,
        )

        total = (
            normalized_weights["price"]
            * price_score
        )

        total += (
            normalized_weights["labour"]
            * labour_score
        )

        total += (
            normalized_weights["lead_time"]
            * lead_time_score
        )

        total += (
            normalized_weights["historical"]
            * historical_score
        )

        if "finish" in normalized_weights:

            total += (
                normalized_weights["finish"]
                * finish_score
            )

        breakdown = ScoreBreakdown(
            price=price_score,
            labour=labour_score,
            lead_time=lead_time_score,
            historical=historical_score,
            finish=finish_score,
            total=total,
        )

        scored.append(
            ScoredCandidate(
                candidate=candidate,
                breakdown=breakdown,
            )
        )

    return scored


def rank_candidates(
    scored_candidates: List[ScoredCandidate],
) -> List[ScoredCandidate]:

    return sorted(
        scored_candidates,
        key=lambda item: (
            -item.breakdown.total,
            item.candidate.list_price_inr,
            item.candidate.lead_time_days,
            item.candidate.labour_minutes,
            item.candidate.sku,
        ),
    )