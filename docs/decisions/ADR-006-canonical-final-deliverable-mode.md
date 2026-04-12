# ADR-006: Canonical final-deliverable mode and naming

## Status
Accepted

## Date
2026-04-12

## Context
Phase 7 needs a clear presentation-ready path that a reviewer can reproduce without reading implementation details. The repository already produces technical diagnostics for Phase 2, Phase 5 and Phase 6, plus a presentation-oriented final product. At this stage the final deliverable must be visually and semantically distinguishable from the technical artifacts, while preserving compatibility for existing outputs and scripts.

## Decision
Introduce a canonical final-deliverable mode with these properties:
- the canonical CLI entry point is `--final-deliverable`,
- canonical outputs use the `presentation_final_deliverable_*` prefix,
- the output metadata carries an explicit `delivery_mode` and `delivery_label`,
- the historical `--final-product` flag remains available as a legacy compatibility alias and keeps the `presentation_final_product_*` prefix,
- the final deliverable continues to reuse the Phase 5 and Phase 6 diagnostics instead of recomputing the physics.

## Consequences
- New users have a single obvious command to reproduce the presentation-ready deliverable.
- The repository now distinguishes canonical deliverables from legacy compatibility outputs and from technical diagnostics.
- Existing scripts can continue using `--final-product` without breaking.
- Tests can verify both the canonical and legacy naming paths.
- Documentation can point to one preferred workflow while still explaining the compatibility layer.

## Alternatives Considered

### Rename `--final-product` in place
- Rejected because it would change the behavior of an existing public flag without leaving an explicit compatibility path.

### Keep only the historical `--final-product` name
- Rejected because Phase 7 needs a clearer canonical name for the actual presentation deliverable.

### Emit only one prefix and infer intent from the content
- Rejected because the file names should make the deliverable category obvious before opening the artifact.
