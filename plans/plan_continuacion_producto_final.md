# Plan: Producto Final de Riesgo de Engelamiento

> Source PRD: [PRD_continuacion_producto_final.md](../specs/PRD_continuacion_producto_final.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Execution model**: the continuation remains a reproducible Python CLI pipeline, not a notebook-first or GUI-first workflow.
- **Scientific baseline**: final-product outputs must consume the already implemented Phase 5 approximate-risk product and Phase 6 heuristic-severity product rather than recomputing thermodynamics independently.
- **Product separation**: the repository should continue to distinguish between technical diagnostics and presentation-oriented final products, with explicit labels for proxy and heuristic outputs.
- **Vertical representation**: flight-oriented views will be expressed through model-level / eta-relative bands unless a future dataset provides the missing variables for geometric altitude.
- **Geographic rendering**: final maps should add visible geographic context to the WRF domain while remaining reproducible within the project environment and dependency model.
- **Output families**: each final-product phase should emit both a presentation artifact and machine-readable metadata that explains what was rendered.
- **Interpretation policy**: aircraft-oriented conclusions must be framed as guided interpretation of relative bands and heuristic/proxy products, not as certified operational icing guidance.
- **Testing strategy**: tests should continue to validate observable outputs, metadata, CLI behavior, and band-selection semantics without coupling to fragile pixel-perfect image assertions.

---

## Phase 1: Final Product Skeleton

**User stories**: 1, 2, 24, 25, 27, 28, 29, 38, 39

### What to build

Create the first tracer-bullet path for the new final-product layer. The pipeline should expose an explicit final-product mode that reuses existing diagnostics, emits clearly named final-product artifacts, and produces a compact summary for a selected time without yet requiring the full polished map design.

### Acceptance criteria

- [ ] The CLI can request a dedicated final-product output for a selected time without replacing the existing Phase 2, 5, and 6 artifacts.
- [ ] The generated outputs are clearly named and labeled as presentation/final-product artifacts rather than low-level diagnostics.
- [ ] The final-product summary states which diagnostic source was used, which time was rendered, and what proxy/heuristic caveats apply.
- [ ] Machine-readable metadata is exported alongside the final-product artifact so the rendered content is traceable.
- [ ] Automated tests verify the new CLI path, artifact naming, and presence of required summary metadata.

---

## Phase 2: Cartographic Base Map

**User stories**: 3, 4, 5, 6, 20, 21, 22, 26, 30, 36

### What to build

Add a presentation-quality map for the selected time that renders the domain with improved geographic context, clearer legend design, stronger visual hierarchy, and a more informative styling than the current binary technical PNGs. This slice should make the final-product figure demoable on its own.

### Acceptance criteria

- [ ] The final-product output includes a map with visible geographic context beyond the raw WRF mask alone.
- [ ] The map legend and title make clear whether the figure shows approximate risk or heuristic severity.
- [ ] The visual design expresses gradation or category meaning more clearly than the current technical PNGs.
- [ ] The figure includes enough annotation or framing to be understandable without opening the Markdown summary first.
- [ ] Automated tests verify artifact generation, output metadata, and figure labeling for the cartographic view.

---

## Phase 3: Vertical Band Product

**User stories**: 10, 11, 12, 17, 18, 19, 31, 32, 34, 37

### What to build

Extend the final-product flow so the user can generate a map or final view conditioned on a selected vertical band of interest. The product should expose relative low/middle/high bands or equivalent eta-based groupings in a way that supports aircraft-oriented interpretation without claiming exact altitude.

### Acceptance criteria

- [ ] The user can select a relative vertical band for the final-product output.
- [ ] The resulting artifact and metadata clearly identify the selected band and its eta/model-level meaning.
- [ ] The summary reports which band is dominant for the selected time and how that relates to the rendered view.
- [ ] The output continues to distinguish relative bands from exact altitude or flight level.
- [ ] Automated tests verify band selection behavior, metadata consistency, and correct handling of empty-band or low-signal cases.

---

## Phase 4: Risk vs Severity Comparison

**User stories**: 7, 14, 15, 23, 31, 33, 35

### What to build

Add an end-to-end slice that lets the user choose between a final product based on the approximate-risk field and one based on the heuristic-severity field. The output should communicate what each product means and why the severity view adds information beyond the approximate binary risk proxy.

### Acceptance criteria

- [ ] The final-product path supports at least two render modes: approximate risk and heuristic severity.
- [ ] Each mode is labeled explicitly in both figure and metadata so the user can tell which methodology is being shown.
- [ ] The summary explains the interpretation difference between the two views without implying false physical certainty.
- [ ] The risk-based and severity-based outputs are both reproducible from the CLI.
- [ ] Automated tests verify mode selection, labels, and output metadata for both render paths.

---

## Phase 5: Aircraft-Oriented Summary

**User stories**: 13, 16, 17, 18, 19, 22, 29, 35, 37

### What to build

Add a concise interpretation layer that accompanies the final figure with a more aircraft-oriented reading for the selected time. This slice should summarize dominant band, spatial coverage, severity class, and the practical cautionary meaning of the result while preserving all caveats about proxy and heuristic status.

### Acceptance criteria

- [ ] The final-product summary includes dominant band, selected-time severity/risk status, and spatial coverage in a compact interpretation block.
- [ ] The summary frames the result in aircraft-oriented language without claiming operational certification.
- [ ] The interpretation block restates the key physical limitations that affect altitude and temperature confidence.
- [ ] The map and summary are coherent when read together as a single deliverable.
- [ ] Automated tests verify the presence and wording category of the interpretation metadata and summary fields.

---

## Phase 6: Highlighted Time Selection

**User stories**: 8, 9, 13, 34, 40

### What to build

Extend the final-product flow so it can identify or accept highlighted times of interest and generate a compact comparative output for those moments. This slice should turn the existing temporal diagnostics into a presentation-oriented shortlist of the most relevant times for the final analysis.

### Acceptance criteria

- [ ] The user can request final-product outputs for more than one relevant time without manually recombining technical artifacts.
- [ ] The output identifies why each highlighted time is relevant, using existing temporal diagnostics such as severity, persistence, or coverage.
- [ ] The comparative output remains concise and presentation-oriented rather than dumping all technical series data.
- [ ] The CLI and metadata remain reproducible for both single-time and highlighted-time modes.
- [ ] Automated tests verify highlighted-time selection behavior and exported summary metadata.

---

## Phase 7: Presentation-Ready Final Deliverable

**User stories**: 3, 4, 13, 20, 22, 35, 36, 37, 38, 39, 40

### What to build

Consolidate the previous slices into the final deliverable path: a presentation-ready output that combines the chosen map, selected band or mode, summary annotations, and final explanatory text into the clearest single artifact the repository can currently produce for the professor.

### Acceptance criteria

- [ ] The repository can generate one canonical final deliverable artifact for the selected analysis mode and time selection.
- [ ] The deliverable is understandable as a standalone result for academic review, with clear title, legend, interpretation, and caveat labeling.
- [ ] The output naming and documentation make it obvious which files are final deliverables versus technical diagnostics.
- [ ] The final-product workflow is documented in the project-facing docs so a new user can reproduce it end to end.
- [ ] Automated tests verify the canonical final-deliverable path and the presence of its required metadata and companion outputs.
