# RuleBound Round 1 — Architecture

## 1. Overview

RuleBound converts a customer room brief into a validated furniture layout and a deterministic INR quote.

Runtime pipeline:

Customer Brief
→ Requirement Extraction
→ Requirement Resolution
→ Product Selection
→ Layout Assembly
→ Layout Validation
→ Deterministic Pricing
→ layout.json + quote.json

Documented runner:

PYTHONPATH=. python3 starter/python/runner.py --input <input-directory> --output <output-directory>

No network service, LLM, external model API, timestamp, random identifier, or probabilistic call is used in the pricing path.

## 2. Requirement Extraction

`app/requirement_extractor.py` converts each customer brief into a structured `RequirementSet`.

It extracts:

- room capacity
- furniture families and quantities
- furniture attributes
- spatial requirements
- customer preferences
- explicit priorities
- evidence from the customer brief

This separates brief interpretation from deterministic downstream planning.

## 3. Requirement Resolution

`app/resolution/` converts extracted requirements into requirements usable by product selection and layout.

Explicit quantities are preserved. Where a quantity can be safely inferred from room capacity and the requirement type, the resolver records the inference and confidence.

For example, paired desks can be resolved from room capacity using two occupants per desk.

Requirements that cannot be safely resolved remain unresolved rather than being silently invented.

## 4. Product Selection

`app/selection/` generates catalog candidates for each resolved furniture requirement and deterministically scores and ranks them.

Selection uses catalog information such as:

- furniture family
- dimensions
- price
- compatible finishes
- requested attributes
- historical-job information where applicable

The highest-ranked candidate is selected.

## 5. Layout Assembly

`app/layout/assembler.py` constructs furniture placements using room geometry and selected products.

The assembler generates candidate positions and searches for a feasible workstation arrangement before committing placements.

Placement identifiers are deterministic (`P-0001`, `P-0002`, etc.) and placement ordering is stable.

Geometry is not weakened merely to satisfy quantity. If requirements cannot be resolved or assembled, that state is preserved for downstream handling.

## 6. Constraint Validation

`app/layout/validator.py` validates the generated layout against room geometry and spatial constraints.

Validation includes placement containment, wall offsets, restricted zones, walkway clearance, desk clearances, and chair pull-out constraints.

Violations are represented structurally rather than hidden.

A generated room can have:

- `valid`
- `invalid`
- `unsatisfiable`

status.

## 7. Arbitration

Arbitration follows explicit customer priorities and hard spatial constraints.

The system does not resolve conflicts using random placement changes or an LLM at runtime.

Decision order:

1. Preserve hard room and safety constraints.
2. Preserve explicit customer priorities.
3. Preserve mandatory furniture requirements where feasible.
4. Resolve inferred requirements only when supported by available evidence.
5. Prefer the deterministic candidate produced by selection and assembly.
6. If requirements cannot be simultaneously satisfied, expose the conflict through layout status and violations rather than silently claiming success.

This makes constraint trade-offs reproducible and auditable.

## 8. Deterministic Pricing

Pricing is performed in `starter/python/runner.py` after layout validation.

Each committed placement is mapped directly to its catalog list price.

For every priced line:

net_goods_inr = quantity × unit_list_price_inr

Each line contains a calculation trace identifying the placement and SKU.

The grand total is the deterministic sum of committed placement prices. Labour and freight are explicitly represented as zero in the current Round 1 implementation.

No timestamp, random value, network call, external model, or probabilistic operation is used in pricing.

## 9. Output Contract

For every input room `<room_id>`, the runner writes:

<output>/<room_id>/layout.json
<output>/<room_id>/quote.json

JSON is written as UTF-8 with sorted keys, two-space indentation, and a trailing newline.

The committed `OUTPUT/` directory contains generated reference outputs for all five released rooms.

## 10. Determinism

The implementation is deterministic for identical input data and code.

Judges can verify this with:

python3 tools/check_determinism.py \
  --command "PYTHONPATH=. python3 starter/python/runner.py --input {input} --output {output}" \
  --input data \
  --work-dir determinism-work

The current verification reports:

DETERMINISTIC: 10 files are byte-identical

Output validation:

python3 tools/validate_output.py OUTPUT

Pack verification:

python3 tools/verify_pack.py
