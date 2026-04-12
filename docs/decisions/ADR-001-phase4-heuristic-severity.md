# ADR-001: Heuristic severity on top of approximate icing risk

## Status
Accepted

## Date
2026-04-12

## Context
Phase 4 extends the project beyond approximate icing risk. The source WRF file does not provide `PB`, so exact thermodynamic diagnosis and altitude-based operational severity are out of scope. We still need a reproducible, incremental product that is useful for interpretation and can be tested with the available variables.

## Decision
Build severity as an explicit heuristic on top of the approximate risk product. The heuristic combines:
- horizontal approximate-risk fraction,
- horizontal liquid-water fraction,
- mixed-phase fraction using `QICE`,
- relative vertical span in model levels,
- temporal persistence accumulated only up to each time step, so future data cannot change earlier scores.

Relative vertical reporting is grouped into eta-based bands: upper, middle and lower. All outputs are labeled as heuristic or approximate, never as exact operational severity.

## Consequences
- The project gains a stable, documented severity layer without needing `PB`.
- The output remains reproducible and testable on synthetic inputs.
- The classification is intentionally relative and should not be interpreted as a validated physical intensity scale.
- Persistence is causal with respect to the time axis: it is cumulative, not global over the full series.
- If a future dataset provides better thermodynamics, this layer can be replaced without changing the earlier phases.

## Alternatives Considered

### Exact physical severity
- Rejected because the source file does not contain the variables needed for an exact reconstruction.

### No severity layer
- Rejected because the PRD explicitly asks for an incremental, documented severity step after the approximate risk product.
