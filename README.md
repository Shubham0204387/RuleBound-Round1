# RuleBound — Round 3 Final Submission

**RuleBound: The Sealed Build Challenge**
**Manufacturer:** Northwind Furnishings (fictional synthetic data)

This repository contains the final Round 3 implementation of the RuleBound challenge solution.

The system converts room briefs and structured catalog/rule data into deterministic furniture layouts and auditable quotes while enforcing spatial, requirement, finish, and pricing constraints.

All challenge records are synthetic.

## Final Solution

The implementation follows a deterministic pipeline:

1. Load the sealed input pack.
2. Extract furniture requirements from room briefs.
3. Resolve explicit and inferable quantities.
4. Select products using deterministic candidate scoring.
5. Arbitrate finishes against requested preferences and product compatibility.
6. Assemble furniture layouts under spatial constraints.
7. Validate geometry and requirements.
8. Apply bounded deterministic repairs when a violation has an improving repair.
9. Escalate when no safe improving repair exists.
10. Generate deterministic, traceable pricing.
11. Block quotes when required information or placement constraints cannot be satisfied safely.
12. Write deterministic JSON outputs.

## Run

From the repository root:

```bash
python3 starter/python/runner.py --input data --output OUTPUT
```

Expected result:

```text
Generated deterministic output for 5 rooms.
```

Each room produces:

```text
OUTPUT/<room_id>/layout.json
OUTPUT/<room_id>/quote.json
```

## Verification

### Verify the input pack

```bash
python3 tools/verify_pack.py
```

### Validate generated output

```bash
python3 tools/validate_output.py OUTPUT
```

### Check determinism

```bash
python3 tools/check_determinism.py --command "python3 starter/python/runner.py --input {input} --output {output}" --input data --work-dir .determinism-check
```

### Run the Python test suite

```bash
PYTHONPATH=. for test in $(find app -name "test_*.py" -type f | sort); do
  python3 "$test" || exit 1
done
```

## Round 3 Improvements

The final implementation adds:

- Deterministic bounded layout repair.
- Explicit escalation instead of unsafe or unbounded repair attempts.
- Stronger geometry validation and executable repair options.
- Finish preference arbitration with compatibility checks.
- Deterministic catalog pricing.
- Finish uplift and quantity-discount calculations using integer INR and basis points.
- Labour and freight calculation with auditable traces.
- Blocking reasons for unresolved requirements.
- Deterministic output ordering and serialization.
- Clean-clone Python runner bootstrap.
- Dependency-free JSON rule loading.
- Written-number quantity extraction.
- Regenerated final outputs for all five rooms.

## Pricing and Auditability

Pricing is integer-based and deterministic.

Each priced line records trace entries for:

- `CATALOG`
- `RB-PRC-009` — quantity discount
- `RB-PRC-010` — finish uplift

Room-level pricing records:

- `RB-PRC-011` — labour
- `RB-PRC-012` — freight

Unsafe or unsupported pricing situations are blocked rather than silently inferred.

See `PRICING_SPEC.md` for the pricing specification.

## Architecture

See `ARCHITECTURE.md` for the final architecture, including:

- requirement arbitration
- product selection
- finish arbitration
- layout assembly
- geometry validation
- deterministic repair
- escalation
- pricing
- output determinism

## Outputs

The committed `OUTPUT/` directory contains generated final outputs for:

- ROOM-01
- ROOM-02
- ROOM-03
- ROOM-04
- ROOM-05

Both layout and quote outputs are validated against the repository output contract.

## Demonstration

**Demo video:** [Watch the RuleBound Round 3 Demo](https://drive.google.com/file/d/1Fof07yqj2pFyq_fHl9Hsy5L8aBi0PRDp/view?usp=sharing)

The final demonstration link will be inserted here before submission.

## Changelog

See `CHANGELOG.md` for the Round 3 implementation changes and verification record.

## Repository Boundaries

The held-back judging set and private Round 3 curveball pack are not included in this repository.

The challenge data is synthetic and contains no real client, employee, or customer information.
