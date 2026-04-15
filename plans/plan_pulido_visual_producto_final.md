# Plan: Pulido Visual Del Producto Final

> Source PRD: issue [#1](https://github.com/ChristianGonper/riesgo-engelamiento-v2/issues/1) - "PRD: pulido visual del producto final y reducción de densidad informativa"

## Architectural decisions

Durable decisions that apply across all phases:

- **CLI contract**: the existing final-product and highlighted-times commands remain the public entrypoints; improvements must keep artifact generation reproducible from the same workflow.
- **Artifact family**: the feature continues to emit three complementary outputs for each run: `PNG` for presentation, `Markdown` for readable report context, and `JSON` for traceability.
- **Content tiers**: the implementation will explicitly separate `figure copy`, `report copy`, and `trace copy` so the PNG stops acting as a full report dump.
- **Scientific boundary**: this work does not reopen the physical Phase 5 or Phase 6 methodology; it only changes presentation behavior and dataset-aware caveat labeling.
- **Capability-aware messaging**: presentation text must adapt to detected dataset capabilities, especially whether `PB` is present, instead of hardcoding stale proxy caveats.
- **Key models**: the plan assumes stable use of the existing final-product summary model, highlighted-times summary model, and a new lightweight dataset-capability presentation model or equivalent abstraction.
- **Views to preserve**: both `approximate-risk` and `heuristic-severity` remain supported presentation views, and highlighted-times remains a separate presentation artifact.

---

## Phase 1: Editorial Contract And Capability Labels

**User stories**: 10, 11, 18, 19, 20, 21, 24, 25, 29, 30, 35, 37, 38

### What to build

Define the end-to-end presentation contract for what belongs in the PNG versus the Markdown and JSON outputs. Add dataset-capability detection for presentation so the generated language and caveats reflect the actual dataset, including whether `PB` is available. Deliver one reproducible run where the outputs already differentiate short figure text from extended report text.

### Acceptance criteria

- [ ] The system distinguishes `figure copy`, `report copy`, and `trace copy` as separate presentation layers.
- [ ] Dataset-aware presentation labels change when `PB` is present versus absent.
- [ ] The PNG no longer depends on long raw metric dumps or full trace text to describe itself.
- [ ] Markdown and JSON still preserve the extended context that is removed from the figure.

### Phase 1 implementation notes

- **Inventory**: the main final-product figure is currently treated as `title and subtitle`, `map panel`, `compact annotation card`, and `short caveat labels`; highlighted-times is treated as `title and subtitle`, `temporal series plot`, `shortlist comparison bars`, and `selection notes card`.
- **Contract**: the short-form figure budget is one title, one subtitle, one compact annotation card, and dataset-aware caveats only as short labels; the report absorbs the extended summary, comparison, interpretation, inventory, and capability note; the trace keeps artifacts, metrics, and outputs.
- **Capabilities**: presentation now detects whether `PB` is present and records a stable `pb-present` / `pb-absent` state for figure-aware copy selection.

---

## Phase 2: Main Figure Hierarchy And Short Annotation Card

**User stories**: 1, 2, 3, 4, 5, 6, 7, 8, 9, 17, 22, 23, 28, 32, 34, 36, 38

### What to build

Rebuild the main final-product figure so the map clearly dominates the composition, the title and subtitle are short and stable, and the annotation panel becomes a compact decision card rather than a report block. This slice should be demoable on both supported render views and should visibly remove the current subtitle overlap and text saturation.

### Acceptance criteria

- [ ] The main figure uses a short title, a single-line subtitle, and a compact annotation card with only high-value messages.
- [ ] The annotation card avoids repeating information already visible in the title, subtitle, legend, or colorbar.
- [ ] The figure remains self-explanatory without embedding long methodological paragraphs.
- [ ] Both `approximate-risk` and `heuristic-severity` views render successfully with the same visual hierarchy.

---

## Phase 3: Highlighted-Times Editorial Redesign

**User stories**: 12, 13, 14, 15, 16, 27, 28, 33, 36, 38

### What to build

Redesign the highlighted-times artifact as a compact editorial figure. Keep the shortlist logic, but present the result as a clean temporal comparison with short labels, compact time formatting, and minimal notes per highlighted time. The resulting figure should communicate why the shortlisted moments matter without trying to include the full selection rationale inside the PNG.

### Acceptance criteria

- [ ] The highlighted-times figure uses concise labels for shortlisted moments and no long paragraph-style notes inside the image.
- [ ] Time formatting on the figure is more compact than the current full ISO strings when that improves readability.
- [ ] The visual emphasis stays on the temporal signal and shortlisted comparisons rather than on explanatory text blocks.
- [ ] The full detailed selection rationale remains available outside the PNG.

### Phase 3 implementation notes

- The highlighted-times PNG now uses compact clock-style labels on the time axis when all moments share the same day, and keeps the detailed ISO labels in the trace payload.
- The shortlist notes card has been reduced to a short reference line plus one compact line per highlighted moment, so the series and shortlist comparison remain the dominant panels.
- The selection rationale stays in Markdown and JSON, not in the visible PNG notes block.

---

## Phase 4: Report And Trace Realignment

**User stories**: 11, 18, 19, 21, 24, 25, 26, 31, 37

### What to build

Align the Markdown and JSON artifacts with the new editorial split so the information removed from the figures is still available in the right place. This slice should make the three output modes complementary instead of duplicative: short presentation text in PNG, readable explanatory prose in Markdown, and exhaustive trace fields in JSON.

### Acceptance criteria

- [ ] Markdown contains the extended interpretation and methodological context that no longer appears in the figure.
- [ ] JSON continues to expose the full trace payload needed for reproducibility.
- [ ] The output family is coherent: the PNG summarizes, the Markdown explains, and the JSON traces.
- [ ] Automatic truncation or summary rules prevent figure text from growing back into report-sized content.

---

## Phase 5: Regression Coverage And Demo Validation

**User stories**: 2, 3, 20, 29, 30, 31, 35, 36

### What to build

Add verification around the new presentation contract so the product stays visually disciplined over time. Cover dataset-capability messaging, content-budget limits, presence of the key figure sections, and continuity of the CLI artifact flow. Finish with a reproducible demo path that exercises the main figure and highlighted-times outputs with the new design.

### Acceptance criteria

- [ ] Tests cover capability-aware caveat labeling for at least one dataset with `PB` and one without it.
- [ ] Tests verify that figure annotations remain within the intended short-form structure rather than regressing to long trace dumps.
- [ ] Tests verify that highlighted-times output uses compact labels and preserves detailed reasoning outside the PNG.
- [ ] The CLI still produces the expected PNG, Markdown, and JSON artifacts for the improved final-product flow.
