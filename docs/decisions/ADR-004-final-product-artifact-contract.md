# ADR-004: Final-product artifact contract for presentation outputs

## Status
Accepted

## Date
2026-04-12

## Context
The repository already produces diagnostic artifacts for Phase 2, Phase 5 and Phase 6. The continuation plan requires a separate presentation-oriented output that can be generated for one selected time without replacing the existing diagnostics.

The new artifact family must remain traceable, clearly labeled as a presentation deliverable, and able to reuse either the approximate-risk view or a spatial heuristic-severity view derived from the existing diagnostics.

## Decision
Introduce a dedicated final-product artifact contract with these properties:
- the artifact family is named as a presentation output, not as another diagnostic phase,
- the required metadata includes selected time, render view, output purpose, caveat labels and source traceability,
- the required metadata includes the generated outputs so the presentation PNG is traceable alongside markdown and JSON,
- the final product reuses Phase 5 for the footprint map and Phase 6 for the severity interpretation, with a derived 2D severity score for the spatial view,
- the CLI exposes an explicit `--final-product` entry path instead of changing the existing diagnostic flow,
- the exported markdown, JSON and presentation PNG are separated from the technical diagnostic outputs.

## Consequences
- The repository gains a clean presentation layer without changing the scientific diagnostics.
- The final product remains traceable to the source diagnostic phase and selected time.
- The presentation PNG can evolve independently from the diagnostic renderers used by Phase 2, Phase 5 and Phase 6.
- The heuristic-severity presentation view now encodes a defensible 2D spatial score instead of repeating the binary footprint.
- Future map-rendering work can build on the same contract without changing the CLI surface again.
- Existing Phase 2, Phase 5 and Phase 6 outputs remain intact.

## Alternatives Considered

### Extend Phase 6 outputs directly
- Rejected because it would blur the distinction between diagnostics and presentation artifacts.

### Add a notebook-only presentation layer
- Rejected because it would not be reproducible from the CLI and would weaken traceability.
