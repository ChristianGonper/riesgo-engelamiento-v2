# ADR-002: Phase 5 as the canonical approximate icing-risk product

## Status
Accepted

## Date
2026-04-12

## Context
The implementation already had a working approximate icing-risk pipeline, but it was labeled as Phase 3 in code, outputs, and documentation. The project plan defines that product as Phase 5. Future work needs a stable canonical name so the approximate thermodynamic proxy, its tests, and its outputs are all traceable against the plan.

## Decision
Promote the approximate icing-risk pipeline to the canonical Phase 5 naming in user-facing code and documentation:
- expose the canonical API through `phase5.py`,
- keep `phase3.py` as a compatibility alias,
- write outputs with `phase5_approximate_icing_risk_*` names,
- label markdown, JSON, and NetCDF artifacts as Phase 5 approximate/proxy products,
- keep the implementation explicit about the approximation because `PB` is unavailable.

## Consequences
- The repository now matches the plan numbering for the approximate icing-risk product.
- Existing callers using `phase3.py` continue to work through compatibility aliases.
- Future work can refer to a single canonical product name instead of juggling two phase numbers.
- If later phases need renumbering, they can be documented separately without changing this decision.

## Alternatives Considered

### Keep the old Phase 3 naming
- Rejected because it keeps the repository out of sync with the plan and makes future documentation harder to read.

### Rename the heuristic severity layer at the same time
- Rejected for this change because the user asked specifically to complete Phase 5; the severity layer can be realigned in a separate follow-up if needed.
