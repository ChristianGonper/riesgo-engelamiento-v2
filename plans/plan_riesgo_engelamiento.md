# Plan: Riesgo de Engelamiento en Aviacion sobre salida WRF

> Source PRD: [PRD_riesgo_engelamiento.md](../specs/PRD_riesgo_engelamiento.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Execution model**: the feature will be implemented as a reproducible Python script pipeline, not as a notebook-first workflow.
- **Primary input**: the initial source dataset is the WRF output file `wrfout_d01_2015-04-17_18_00_00_corte`.
- **Data access**: NetCDF reading and validation will be handled through `xarray`.
- **Core fields**: the durable input fields are `QCLOUD`, `QRAIN`, `QICE`, `T`, `P`, `ZNW`, `XLAT`, `XLONG`, and `XTIME`.
- **Robust diagnostics**: robust outputs are limited to diagnostics directly supported by present variables, especially liquid-water presence, time evolution, and relative vertical structure.
- **Approximate diagnostics**: icing risk will be produced as an explicitly approximate product because `PB` is unavailable and temperature reconstruction cannot be exact.
- **Vertical representation**: vertical outputs will be expressed in model levels or eta-relative coordinates, not geometric altitude.
- **Key models**: the implementation will revolve around dataset metadata, derived liquid fields, mixed-phase indicators, approximate thermodynamic fields, and risk masks.
- **Output families**: each phase should produce both machine-readable results and directly interpretable summaries or figures.
- **Testing strategy**: tests will focus on observable behavior with modular synthetic inputs or small subsets, avoiding heavy dependence on the full dataset in every run.

---

## Phase 1: Base reproducible y validacion del dataset

**User stories**: 1, 2, 14, 17, 22, 27, 35

### What to build

Create the end-to-end project skeleton that can open the WRF dataset, validate required variables and dimensions, record core assumptions such as `T0 = 300 K`, and emit a reproducible summary of available inputs and known limitations.

### Acceptance criteria

- [ ] Running the main script against the repository dataset completes without manual intervention.
- [ ] The pipeline reports the presence or absence of required variables and dimensions with clear error messages.
- [ ] The pipeline emits a compact summary of times, grid shape, vertical levels, and supported diagnostics.
- [ ] Core assumptions and dataset limitations are documented in a central project-facing output.
- [ ] A minimal automated test covers dataset validation behavior on both valid and invalid inputs.

---

## Phase 2: Diagnostico binario de hidrometeoros liquidos y salidas base

**User stories**: 3, 5, 7, 8, 11, 12, 16, 23, 25, 29, 31

### What to build

Build the first robust scientific slice: for a selected time step, derive liquid-water presence from `QCLOUD + QRAIN`, produce a binary horizontal risk-candidate mask, generate a map-ready output, and summarize how many grid cells contain liquid water or no signal.

### Acceptance criteria

- [ ] The user can target a single time step and obtain a binary horizontal liquid-presence product.
- [ ] The pipeline correctly reports when a selected time has no liquid hydrometeors.
- [ ] A reproducible map or equivalent visual output is generated from the derived field.
- [ ] A textual or tabular summary includes the count of cells with liquid presence for the selected time.
- [ ] Automated tests verify liquid-mask behavior for `QCLOUD`, `QRAIN`, combined cases, and empty cases.

---

## Phase 3: Analisis temporal del dominio

**User stories**: 6, 7, 8, 12, 22, 24, 25

### What to build

Extend the same end-to-end flow across all available times so the project can summarize temporal evolution of liquid presence, identify active versus inactive time steps, and export a compact time-series product suitable for later phases.

### Acceptance criteria

- [ ] The pipeline can process all available times in one run.
- [ ] The output includes a time-indexed summary of whether liquid is present in the domain at each instant.
- [ ] The output includes a time-indexed count or fraction of horizontal cells with liquid presence.
- [ ] The temporal summary can be exported for reuse in downstream phases.
- [ ] Automated tests verify that temporal aggregation preserves expected coordinates and handles empty times correctly.

---

## Phase 4: Analisis vertical relativo y fase mixta

**User stories**: 4, 9, 10, 16, 22, 25, 32, 33, 34

### What to build

Add a vertical slice through the same workflow by characterizing where liquid and ice occur across model levels, using `bottom_top` and `ZNW` to produce relative vertical occupancy, mixed-phase indicators, and summaries of which levels are active over time.

### Acceptance criteria

- [ ] The pipeline reports which model levels contain liquid hydrometeors for a chosen time and across the full series.
- [ ] The pipeline reports where liquid and ice coexist as a mixed-phase indicator.
- [ ] The output distinguishes relative contributions from `QCLOUD`, `QRAIN`, and `QICE`.
- [ ] Vertical results are clearly labeled as model-level or eta-relative outputs rather than altitude products.
- [ ] Automated tests verify vertical aggregation and mixed-phase logic on controlled synthetic inputs.

---

## Phase 5: Riesgo de engelamiento aproximado documentado

**User stories**: 13, 15, 18, 19, 20, 21, 26, 27, 28, 30, 31

### What to build

Introduce the first approximate icing-risk product by reconstructing total potential temperature from `T`, applying a documented pressure approximation strategy, deriving an approximate air temperature, and combining that estimate with liquid-water presence to produce an explicitly labeled potential icing-risk mask and summary.

### Acceptance criteria

- [ ] The pipeline computes `theta = T + 300` and applies a documented approximation for total pressure.
- [ ] The pipeline produces an approximate temperature-derived binary icing-risk mask based on liquid presence and estimated subzero conditions.
- [ ] All outputs generated from this phase are explicitly marked as approximate or proxy products.
- [ ] The run output explains why the estimate is approximate and why exact reconstruction is not possible with the available dataset.
- [ ] Automated tests verify approximation flow behavior, labeling, and failure modes when required approximation inputs are missing.

---

## Phase 6: Severidad heuristica y rangos relativos de niveles

**User stories**: 16, 18, 22, 25, 26, 34, 35

### What to build

Build a heuristic post-processing layer on top of the approximate risk product to classify relative severity, summarize persistence and vertical spread, and define relative level ranges where the event is more likely to be operationally relevant, all while preserving explicit documentation of uncertainty.

### Acceptance criteria

- [ ] The pipeline assigns heuristic severity categories using documented thresholds or rules.
- [ ] The output summarizes relative level ranges or grouped model layers associated with elevated approximate risk.
- [ ] Severity outputs incorporate at least liquid amount, persistence, or mixed-phase context as documented heuristics.
- [ ] The resulting products remain clearly separated from exact physical diagnoses.
- [ ] Automated tests verify that severity classification is stable for controlled threshold scenarios and remains configurable.
