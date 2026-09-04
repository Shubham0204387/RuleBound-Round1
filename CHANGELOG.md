# Changelog

## Round 3 — Final Submission

### Added
- Added deterministic bounded layout repair with explicit escalation when no improving repair exists.
- Added finish arbitration based on requested preferences and product compatibility.
- Added deterministic pricing with catalog pricing, finish uplift, quantity discounts, labour, freight, and auditable pricing traces.
- Added explicit blocking reasons for unsatisfied requirements.
- Added escalation metadata to layout outputs.
- Added clean-runner bootstrap so the Python runner works from a fresh repository clone.
- Removed the runtime YAML dependency by loading the authoritative JSON rules file directly.
- Added written-number extraction support for furniture quantities.
- Regenerated deterministic outputs for all five rooms.

### Improved
- Added bounded workstation and chair-placement search to prevent unbounded search.
- Strengthened geometry validation with executable repair options.
- Improved deterministic output serialization and room ordering.
- Revised architecture documentation to describe the final arbitration, repair, pricing, and determinism pipeline.

### Fixed
- Prevented ROOM-05 workstation search from stalling during chair assignment.
- Ensured unresolved requirements propagate into blocking quote reasons.
- Ensured pricing is blocked when required product/finish information is missing or incompatible.

### Verification
- Official pack verification: PASS
- Full application test suite: PASS
- Determinism verification: 10/10 output files byte-identical
- Clean-machine execution: pending final release-commit verification
- Pricing arithmetic and trace audits: PASS