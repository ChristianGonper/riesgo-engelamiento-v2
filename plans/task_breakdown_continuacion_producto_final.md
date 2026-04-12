# Implementation Plan: Producto Final de Riesgo de Engelamiento

## Overview

Vamos a transformar el pipeline diagnóstico ya implementado en un producto final más útil para presentación académica y lectura aeronáutica guiada. La base científica ya existe en el repositorio: validación del dataset, máscara líquida, riesgo aproximado y severidad heurística. El objetivo de este desglose es construir, paso a paso, una capa final de visualización y síntesis que reutilice esos productos y los convierta en mapas y resúmenes finales reproducibles desde la CLI.

## Architecture Decisions

- La nueva capa de producto final debe consumir Phase 5 y Phase 6 ya calculadas; no debe reimplementar el cálculo termodinámico ni heurístico.
- La CLI debe conservar el flujo actual y añadir una ruta explícita de “producto final”, sin romper los artefactos diagnósticos existentes.
- La representación vertical seguirá siendo relativa al modelo o a bandas eta; no se afirmará altitud geométrica exacta.
- Los artefactos finales deben diferenciarse claramente de los artefactos técnicos mediante nomenclatura, metadatos y texto visible.
- La parte cartográfica y la parte de resumen interpretativo deben estar separadas para mantener testabilidad.
- Las pruebas deben validar semántica observable, metadatos y flujo CLI, no hacer snapshot visual píxel a píxel.

## Dependency Graph

```text
Final-product CLI/config
    │
    ├── Final-product data model + metadata
    │       │
    │       ├── Final-product summary rendering
    │       ├── Final-product map rendering
    │       └── Final-product export naming
    │
    ├── Band-selection layer
    │       │
    │       └── Aircraft-oriented interpretation layer
    │
    └── Highlighted-time selection
            │
            └── Canonical presentation-ready deliverable
```

## Task List

### Phase 1: Foundation

## Task 1: Define final-product artifact contract

**Description:** Introduce the conceptual contract for final-product outputs so the pipeline can generate a new family of artifacts without mixing them with existing diagnostic outputs. This task establishes the metadata shape, naming rules, and output purpose for the selected-time final product.

**Acceptance criteria:**
- [ ] There is a documented final-product artifact concept distinct from Phase 2, 5, and 6 diagnostics.
- [ ] The contract defines required metadata fields such as source mode, selected time, caveat labels, and output purpose.
- [ ] The naming convention clearly separates final artifacts from technical diagnostics.

**Verification:**
- [ ] Manual check: the plan/documentation of the artifact contract is understandable without reading implementation details.
- [ ] Manual check: the contract can support both approximate-risk and heuristic-severity views.

**Dependencies:** None

**Files likely touched:**
- `README.md`
- `src/riesgo_engelamiento/config.py`
- `docs/decisions/`

**Estimated scope:** S

## Task 2: Add CLI entry path for final-product generation

**Description:** Add a reproducible CLI path that requests final-product generation for a selected time while preserving the current diagnostic outputs. This is the tracer-bullet entry point for the whole continuation.

**Acceptance criteria:**
- [ ] The CLI exposes an explicit option or mode to generate final-product artifacts.
- [ ] Running the CLI in final-product mode does not remove or redefine the existing diagnostic phases.
- [ ] The CLI output makes clear which artifact is the new final-product output.

**Verification:**
- [ ] Manual check: the CLI help text exposes the new final-product path clearly.
- [ ] Manual check: a local run produces a dedicated final-product artifact.
- [ ] Tests pass: targeted CLI/output tests.

**Dependencies:** Task 1

**Files likely touched:**
- `src/riesgo_engelamiento/cli.py`
- `src/riesgo_engelamiento/config.py`
- `tests/test_dataset_validation.py`

**Estimated scope:** M

## Task 3: Create final-product summary model and exports

**Description:** Build the first reusable data/summary layer for the final-product path. This task should produce structured metadata and a concise summary artifact for the selected time, still before the polished cartographic view is complete.

**Acceptance criteria:**
- [ ] The final-product path exports machine-readable metadata for the selected time.
- [ ] The summary states diagnostic source, selected time, render mode, and caveat text.
- [ ] The summary is reproducible and separate from the diagnostic markdown outputs.

**Verification:**
- [ ] Manual check: generated metadata is traceable and self-explanatory.
- [ ] Tests pass: final-product metadata/export tests.

**Dependencies:** Task 2

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** M

### Checkpoint: Foundation

- [ ] Final-product mode exists end to end for a selected time
- [ ] A dedicated artifact and summary are exported
- [ ] Tests pass for the new path before map polish begins
- [ ] Review with human before proceeding to cartographic work

### Phase 2: Cartographic Base

## Task 4: Add reusable cartographic styling layer

**Description:** Introduce a dedicated styling/configuration layer for final maps so color ramps, titles, legends, labels, and layout decisions are centralized instead of embedded in ad hoc rendering code.

**Acceptance criteria:**
- [ ] Final-map styling choices are centralized in configuration or a dedicated rendering layer.
- [ ] The styling supports both approximate-risk and heuristic-severity visual modes.
- [ ] Visual configuration can evolve without changing scientific calculations.

**Verification:**
- [ ] Manual check: visual defaults are defined in one place.
- [ ] Manual check: both render modes can consume the same styling layer.

**Dependencies:** Task 3

**Files likely touched:**
- `src/riesgo_engelamiento/config.py`
- `src/riesgo_engelamiento/`

**Estimated scope:** S

## Task 5: Render first presentation-quality final map

**Description:** Implement the first real final-product map for a selected time with better geographic context, stronger legend design, and more interpretable presentation than the existing technical PNGs. This should be demoable as the first “showable” output.

**Acceptance criteria:**
- [ ] The final-product artifact includes a map with visible geographic context.
- [ ] The map title and legend identify whether the view is approximate risk or heuristic severity.
- [ ] The map is visually more informative than the current binary technical output.

**Verification:**
- [ ] Manual check: compare the new final map against the current technical PNGs.
- [ ] Manual check: the figure is understandable without opening the code.
- [ ] Tests pass: artifact generation and metadata tests.

**Dependencies:** Task 4

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`
- `outputs/` (manual local verification only)

**Estimated scope:** M

## Task 6: Add self-contained figure annotations

**Description:** Make the final map more self-sufficient by adding on-figure text or summary boxes that communicate the essential context directly on the PNG.

**Acceptance criteria:**
- [ ] The figure includes enough annotation to explain selected time, mode, and caveat level.
- [ ] The annotation does not overwhelm the map or hide the main signal.
- [ ] The summary information shown on the figure is consistent with the exported metadata.

**Verification:**
- [ ] Manual check: the figure can be interpreted standalone.
- [ ] Tests pass: metadata/labeling tests remain green.

**Dependencies:** Task 5

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

### Checkpoint: Cartographic Base

- [ ] The repository can generate a presentable final map for one selected time
- [ ] Labels, legend, and annotations are coherent
- [ ] Final-product metadata still matches the rendered figure
- [ ] Review the visual quality with the human before adding band logic

### Phase 3: Vertical Band Product

## Task 7: Define presentation-oriented vertical band selection contract

**Description:** Formalize how the final-product layer selects and names vertical bands so users can request low/middle/high or equivalent relative layers consistently.

**Acceptance criteria:**
- [ ] The final-product layer accepts explicit band selection input.
- [ ] Band names and semantics are documented as model-relative, not altitude-exact.
- [ ] The contract supports both “selected band” and “dominant band” reporting.

**Verification:**
- [ ] Manual check: band names are understandable to a reader outside the code.
- [ ] Tests pass: band-selection contract tests.

**Dependencies:** Task 6

**Files likely touched:**
- `src/riesgo_engelamiento/config.py`
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

## Task 8: Render final-product map for a selected vertical band

**Description:** Extend the final map path so it can condition the view on a selected vertical band and communicate clearly which relative layer is being shown.

**Acceptance criteria:**
- [ ] A user can generate a final-product map for a selected relative band.
- [ ] The artifact and metadata identify the selected band unambiguously.
- [ ] Empty-band or low-signal cases produce a valid, understandable output.

**Verification:**
- [ ] Manual check: render at least one populated band and one sparse/empty band.
- [ ] Tests pass: band-output and metadata tests.

**Dependencies:** Task 7

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/test_phase6.py`
- `tests/`

**Estimated scope:** M

## Task 9: Add dominant-band summary to final-product outputs

**Description:** Connect the existing severity structure to the final-product summary so the system can state which band dominates and how that relates to the rendered map.

**Acceptance criteria:**
- [ ] The final-product summary includes dominant band information for the selected time.
- [ ] The rendered output and metadata remain consistent when a selected band differs from the dominant band.
- [ ] Band interpretation remains explicitly relative to the model.

**Verification:**
- [ ] Manual check: summary and figure tell a coherent story.
- [ ] Tests pass: summary metadata tests.

**Dependencies:** Task 8

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

### Checkpoint: Vertical Band Product

- [ ] Final-product outputs work for total-domain and selected-band views
- [ ] Band metadata and summaries are coherent
- [ ] Empty-band scenarios remain interpretable

### Phase 4: Comparison Modes

## Task 10: Add render mode selection for approximate risk vs heuristic severity

**Description:** Allow the user to choose whether the final-product map is based on the approximate-risk field or the heuristic-severity field, preserving explicit methodology labeling.

**Acceptance criteria:**
- [ ] The final-product path supports at least two render modes.
- [ ] Each mode is clearly named in artifacts, metadata, and figure labels.
- [ ] Mode selection does not require changing the underlying diagnostic pipeline.

**Verification:**
- [ ] Manual check: render one artifact in each mode and compare outputs.
- [ ] Tests pass: mode-selection tests.

**Dependencies:** Task 9

**Files likely touched:**
- `src/riesgo_engelamiento/cli.py`
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** M

## Task 11: Add comparative explanatory summary

**Description:** Add a summary layer that explains what changes when the user selects approximate-risk mode versus heuristic-severity mode, so the final output is interpretable and academically defensible.

**Acceptance criteria:**
- [ ] The summary explains the interpretation difference between risk and severity views.
- [ ] The wording preserves proxy and heuristic caveats.
- [ ] The metadata records which explanatory path was used.

**Verification:**
- [ ] Manual check: the two modes are distinguishable without reading implementation details.
- [ ] Tests pass: summary wording/metadata tests.

**Dependencies:** Task 10

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`
- `README.md`

**Estimated scope:** S

### Phase 5: Aircraft-Oriented Interpretation

## Task 12: Define aircraft-oriented interpretation block

**Description:** Create the structured interpretation block that translates the selected-time result into a more aircraft-oriented reading while remaining non-operational and caveated.

**Acceptance criteria:**
- [ ] The final-product summary includes a dedicated aircraft-oriented interpretation section.
- [ ] The wording explicitly avoids operational-certification language.
- [ ] The interpretation references selected band, spatial coverage, and severity/risk status.

**Verification:**
- [ ] Manual check: the text sounds applied but still technically honest.
- [ ] Tests pass: interpretation metadata/summary tests.

**Dependencies:** Task 11

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

## Task 13: Integrate dominant band, coverage, and caveats into one compact final summary

**Description:** Consolidate the aircraft-oriented interpretation, band data, and caveat messaging into a compact summary block that can accompany the figure as the human-facing explanation.

**Acceptance criteria:**
- [ ] The final summary presents dominant band, coverage, selected mode, and caveats in one coherent block.
- [ ] The map and summary together can be used as a single deliverable for one time.
- [ ] The summary remains concise enough for presentation use.

**Verification:**
- [ ] Manual check: the map + summary pair is understandable standalone.
- [ ] Tests pass: final-summary export tests.

**Dependencies:** Task 12

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

### Checkpoint: Aircraft-Oriented Interpretation

- [ ] There is now a map plus a compact interpretation block
- [ ] The output is useful for academic presentation, not just engineering inspection
- [ ] Caveats remain explicit and visible

### Phase 6: Highlighted Times

## Task 14: Define highlighted-time selection rules

**Description:** Decide and encode how the final-product layer selects or accepts highlighted times of interest using the temporal diagnostics already available in the repository.

**Acceptance criteria:**
- [ ] Highlighted-time selection can be requested explicitly or derived from existing temporal diagnostics.
- [ ] The selection rule is documented and reproducible.
- [ ] The metadata records why each highlighted time was chosen.

**Verification:**
- [ ] Manual check: the time-selection rule is easy to explain to a human.
- [ ] Tests pass: highlighted-time rule tests.

**Dependencies:** Task 13

**Files likely touched:**
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

## Task 15: Generate compact comparative output for highlighted times

**Description:** Build the first multi-time final-product output that focuses on a short list of relevant times rather than dumping the whole series.

**Acceptance criteria:**
- [ ] The user can generate a concise comparative final-product output for more than one highlighted time.
- [ ] The output explains why those times are relevant.
- [ ] The comparative output remains presentation-oriented rather than purely technical.

**Verification:**
- [ ] Manual check: the comparative output is concise and readable.
- [ ] Tests pass: multi-time final-product tests.

**Dependencies:** Task 14

**Files likely touched:**
- `src/riesgo_engelamiento/cli.py`
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** M

### Phase 7: Presentation-Ready Deliverable

## Task 16: Define canonical final-deliverable mode and naming

**Description:** Consolidate the previous work into one canonical final-deliverable path so a user can generate the clearest current project result without deciding between many intermediate artifacts.

**Acceptance criteria:**
- [ ] The repository exposes one canonical final-deliverable mode.
- [ ] Artifact names and docs clearly distinguish final deliverables from technical diagnostics.
- [ ] The deliverable mode supports the chosen analysis mode and time-selection strategy.

**Verification:**
- [ ] Manual check: a new user can tell which file is the final deliverable.
- [ ] Tests pass: canonical-path tests.

**Dependencies:** Task 15

**Files likely touched:**
- `README.md`
- `src/riesgo_engelamiento/cli.py`
- `src/riesgo_engelamiento/`
- `tests/`

**Estimated scope:** S

## Task 17: Document and verify presentation-ready workflow end to end

**Description:** Close the loop by documenting how to produce the final deliverable and ensuring the full end-to-end workflow is reproducible and reviewable.

**Acceptance criteria:**
- [ ] Project-facing documentation explains how to generate the final deliverable end to end.
- [ ] The final workflow is reproducible from a clean run of the CLI.
- [ ] The required metadata and companion outputs are present for review.

**Verification:**
- [ ] Manual check: follow the docs from scratch and generate the deliverable.
- [ ] Tests pass: end-to-end final-product path tests.
- [ ] Manual check: the deliverable is suitable for sharing with the professor.

**Dependencies:** Task 16

**Files likely touched:**
- `README.md`
- `specs/`
- `plans/`
- `tests/`

**Estimated scope:** S

### Checkpoint: Complete

- [ ] All final-product tasks are implemented or consciously deferred
- [ ] The canonical final deliverable is reproducible
- [ ] Diagnostic outputs and legacy compatibility remain intact
- [ ] The result is ready for human review before implementation or delegation

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cartographic dependency adds setup friction or portability issues | High | Prefer incremental styling first; only add heavier geo dependencies if the visual gain is clearly worth it |
| Final-product layer starts recomputing scientific logic | High | Enforce reuse of Phase 5 and Phase 6 outputs through a dedicated contract |
| “Aircraft-oriented” language becomes too operational for the data quality | High | Keep wording explicitly interpretive and caveated in both map and summary |
| Vertical-band UX becomes confusing without real altitude | Medium | Use stable relative band names and repeat eta/model-level caveats visibly |
| Comparative/multi-time output becomes too dense for presentation | Medium | Limit highlighted times and keep summaries compact by design |

## Open Questions

- ¿Queremos priorizar una mejora visual sin nuevas dependencias geográficas o aceptamos incorporar una librería cartográfica adicional si mejora claramente el mapa?
- ¿El profesor valoraría más un mapa único muy pulido o un pequeño panel comparativo con varios tiempos destacados?
- ¿Para la lectura “orientada a aeronaves” prefieres hablar en bandas baja/media/alta o en rangos de niveles del modelo con una explicación adicional?
- ¿Quieres que la primera implementación del producto final se base antes en `Phase 6` por ser más expresiva, o en `Phase 5` por ser metodológicamente más directa?

## Verification

- [ ] Every task has acceptance criteria
- [ ] Every task has a verification step
- [ ] Task dependencies are identified and ordered correctly
- [ ] No task is obviously XL-sized
- [ ] Checkpoints exist between major phases
- [ ] The human has reviewed and approved the plan
