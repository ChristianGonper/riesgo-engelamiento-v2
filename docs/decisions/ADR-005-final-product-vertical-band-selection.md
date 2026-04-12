# ADR-005: Final-product vertical band selection contract

## Status
Accepted

## Date
2026-04-12

## Context
The final-product layer now supports a presentation-oriented map that can be conditioned on a relative vertical band. The project still lacks geometric altitude variables, so the band choice must stay anchored to model-relative eta groups while remaining easy to interpret in the CLI, metadata and figure labels.

The continuation also requires the final product to report the dominant band for the selected time, even when the rendered band is chosen explicitly by the user.

## Decision
Add an explicit vertical-band contract to the final-product layer with these rules:
- the CLI accepts a band request separate from the render view,
- `dominant` is a valid request that resolves to the dominant band from the selected time,
- explicit bands remain model-relative eta groups and are not translated to exact altitude,
- the exported artifact metadata records both the requested band and the resolved band,
- the map, markdown and JSON all identify the dominant band and how it relates to the rendered band,
- empty or low-signal band cases remain valid outputs and are labeled honestly rather than forcing a synthetic altitude interpretation.

## Consequences
- Users can generate final-product outputs for a chosen relative band without changing the scientific pipeline.
- The summary can state both the rendered band and the dominant band for the selected time.
- The contract remains compatible with future geometric-altitude work if new variables become available later.
- Tests can validate band selection semantics directly from the exported metadata.

## Alternatives Considered

### Encode only the dominant band
- Rejected because users need to inspect non-dominant bands as part of the presentation workflow.

### Translate bands into altitude labels
- Rejected because the repository still lacks the variables needed for a defensible geometric-altitude interpretation.
