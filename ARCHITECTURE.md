# RuleBound Round 3 — Architecture

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

python3 starter/python/runner.py --input <input-directory> --output <output-directory>

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

Arbitration is the deterministic seam between generated proposals and the rule-enforced layout.

The generative/extraction stages may propose requirements and the layout assembler may propose candidate placements, but they do not get to declare a layout valid. The deterministic validation and repair layer is authoritative.

A candidate layout follows this sequence:

1. Generate/assemble a deterministic candidate layout.
2. Validate every committed placement against the room and spatial rules.
3. Represent each violation as a structured `Violation`.
4. For a violation, generate structured `RepairOption` candidates when a deterministic repair is available.
5. Score and order repair candidates deterministically.
6. Trial a candidate repair on a snapshot of the layout.
7. Revalidate the complete layout.
8. Accept the repair only if the global termination measure strictly decreases.
9. Restore the previous layout when a candidate does not strictly improve the measure.
10. Continue until the layout is valid, no improving repair exists, or the bounded repair-step limit is reached.
11. If the layout cannot become valid within the bounded loop, attach a structured escalation object rather than silently claiming success.

The system does not resolve conflicts using random placement changes or an LLM at runtime.

### Arbitration priorities

The deterministic arbitration policy is:

1. Preserve hard room and safety constraints.
2. Preserve explicit customer priorities.
3. Preserve mandatory furniture requirements where feasible.
4. Resolve inferred requirements only when supported by available evidence.
5. Prefer the deterministic candidate produced by selection and assembly.
6. Repair geometric violations only through structured, executable repair options.
7. Never accept a repair that does not strictly improve the termination measure.
8. If requirements or constraints cannot be simultaneously satisfied, expose the conflict through layout status, violations, and escalation rather than silently claiming success.

### Repair-option arbitration

Validators produce executable `RepairOption` objects rather than directly mutating the layout.

A repair option contains:

- action type
- human-readable description
- deterministic score
- structured parameters such as placement identifier and movement vector

The repair engine considers all executable options available for the current violations.

Options are ordered deterministically using:

1. higher repair score first
2. violation identifier
3. action type
4. placement identifier
5. movement parameters
6. description

This means that equal-scoring or otherwise equivalent repair candidates are resolved by stable data-derived tie-breakers rather than iteration order, randomness, or model output.

Each candidate is evaluated transactionally. The current layout is snapshotted, the repair is applied, and the complete layout is revalidated. The candidate is committed only when the resulting global termination measure is strictly smaller than the previous measure. Otherwise the snapshot is restored.

### Termination measure

The repair loop uses a weighted scalar measure derived from the current violations.

Requirement violations receive a very large fixed weight so that unresolved hard requirements dominate geometric violations. Unknown violation types receive a fixed deterministic weight.

For geometric violations, the measure uses deterministic quantities such as:

- overlap area for placement overlap violations
- required clearance minus measured clearance for clearance violations
- required wall offset minus measured wall offset for wall-offset violations
- a fixed positive penalty for containment and other geometry violations

The total measure is the deterministic sum of these violation penalties.

A repair is accepted only when:

`new_measure < current_measure`

Therefore every accepted repair strictly decreases the termination measure. A repair that merely changes the violation without improving the global measure is rejected and rolled back.

The repair loop is bounded by `MAX_REPAIR_STEPS = 12`. This prevents unbounded search or oscillation.

### Escalation

If no executable repair option produces a strictly smaller termination measure, or the maximum repair-step bound is reached before the layout becomes valid, the engine stops.

It creates a structured escalation object containing:

- `escalation_id`
- `room_id`
- `reason`
- `violation_ids`
- `termination_measure`

The resulting layout is marked `unsatisfiable` when unresolved violations remain.

This provides a deterministic and auditable failure path instead of hiding unresolved constraints.

### Finish preference arbitration

Finish preferences are extracted from the customer brief and considered before the deterministic finish fallback.

- A known preference is mapped to a catalog finish only when the repository provides an explicit semantic mapping.
- A preferred finish is accepted only when it is compatible with every selected product family in the room.
- The system never invents catalog semantics. For example, `durable_neutral` is extracted as a preference, but the finish catalog does not define a durability attribute, so it is not silently mapped to an arbitrary finish.
- When no preferred finish can be used, the deterministic fallback considers finishes compatible with every selected product family.
- The fallback selects the finish with the lowest `uplift_bps`; ties are resolved by `finish_id`.
- Therefore an unmapped preference such as `durable_neutral` can still produce a deterministic, priceable result without falsely claiming an unsupported semantic match.

This makes constraint trade-offs, repair arbitration, termination, escalation, and finish arbitration reproducible and auditable.

## 8. Deterministic Pricing

Pricing is performed in `starter/python/runner.py` after layout validation and repair.

Only committed placements are eligible for pricing. Quote lines are aggregated deterministically by `SKU + finish_id`.

### Goods pricing

For each SKU + finish group:

`base_amount_inr = unit_list_price_inr × quantity`

Finish uplift is calculated using the catalog finish's `uplift_bps`:

`finish_uplift_inr = round_half_up(base_amount_inr × uplift_bps / 10000)`

Quantity discounts are applied to the base amount:

- quantity < 5 → 0 bps
- quantity 5–9 → 300 bps
- quantity 10–19 → 700 bps
- quantity ≥ 20 → 1000 bps

`quantity_discount_inr = round_half_up(base_amount_inr × discount_bps / 10000)`

The resulting net goods amount is:

`net_goods_inr = base_amount_inr + finish_uplift_inr - quantity_discount_inr`

All monetary calculations use integer INR arithmetic with round-half-up behavior rather than floating-point rounding.

### Labour pricing

Total labour minutes are calculated from the catalog labour minutes for each priced product:

`total_labour_minutes = Σ(product.labour_minutes × quantity)`

The deterministic labour rate is:

- ≤ 240 minutes → ₹900/hour
- 241–480 minutes → ₹800/hour
- > 480 minutes → ₹750/hour

Labour is calculated as:

`labour_inr = round_half_up(total_labour_minutes × labour_rate / 60)`

### Freight pricing

Freight is calculated from the goods total after finish uplifts and quantity discounts:

- goods total ≤ ₹100,000 → ₹5,000 flat
- goods total ≤ ₹250,000 → ₹9,000 flat
- goods total > ₹250,000 → 400 bps (4%) of goods total

For the percentage band:

`freight_inr = round_half_up(goods_total × 400 / 10000)`

### Grand total

The final deterministic quote total is:

`grand_total_inr = goods_total + labour_inr + freight_inr`

### Price trace and blocking

Every priced line contains a calculation trace identifying:

- catalog unit price and quantity
- finish uplift rule `RB-PRC-010`
- quantity discount rule `RB-PRC-009`

The summary trace records:

- labour rule `RB-PRC-011`
- freight rule `RB-PRC-012`

If a committed placement cannot be priced, the quote is blocked rather than silently omitting the placement. `RB-PRC-013` records the blocking condition.

Pricing is also blocked when:

- the SKU has no catalog price
- the referenced finish does not exist or is not priced
- the finish is incompatible with the product family
- the layout remains invalid or unsatisfiable

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
  --command "python3 starter/python/runner.py --input {input} --output {output}" \
  --input data \
  --work-dir determinism-work

The current verification reports:

DETERMINISTIC: 10 files are byte-identical

Output validation:

python3 tools/validate_output.py OUTPUT

Pack verification:

python3 tools/verify_pack.py
