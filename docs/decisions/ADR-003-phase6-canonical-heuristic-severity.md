# ADR-003: Canonical Phase 6 naming for heuristic severity

## Status
Accepted

## Date
2026-04-12

## Context
The heuristic severity layer was implemented before the plan numbering was finalized in user-facing code. The plan now defines that layer as Phase 6: it sits on top of the approximate icing-risk proxy, combines liquid, mixed-phase, persistence and relative vertical-band heuristics, and must remain explicitly approximate rather than an exact physical diagnosis.

We need the repository to match the plan numbering in its canonical API, outputs and documentation without breaking existing callers that still import the historical `phase4` module.

## Decision
Make Phase 6 the canonical public name for the heuristic severity layer:
- expose the canonical API through `phase6.py`,
- write canonical outputs as `phase6_heuristic_severity_*`,
- label markdown, JSON and NetCDF artifacts as Phase 6 heuristic/proxy products,
- keep `phase4.py` as a compatibility alias for legacy callers,
- keep the implementation explicit about the heuristic and approximate nature of the product.

## Consequences
- User-facing code and documentation now match the plan numbering.
- Existing callers can continue using `phase4.py` while the repository migrates to the canonical name.
- Tests can assert both the canonical Phase 6 outputs and the legacy Phase 4 alias behavior.
- The heuristic layer remains intentionally relative and should not be confused with an exact operational severity diagnostic.

## Alternatives Considered

### Keep Phase 4 as the public name
- Rejected because it diverges from the plan and makes future documentation harder to reconcile.

### Rename the implementation file without a compatibility alias
- Rejected because it would break existing callers and regress the explicit compatibility guarantee already established for earlier phase renumbering.
