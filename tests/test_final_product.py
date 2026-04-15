from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import pytest
import xarray as xr

from riesgo_engelamiento import cli
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.final_product import (
    detect_dataset_presentation_capabilities,
    build_final_product_figure,
    build_final_product_summary,
    build_highlighted_times_figure,
    build_highlighted_times_summary,
    write_final_product_outputs,
    write_highlighted_times_outputs,
)
from riesgo_engelamiento.phase5 import build_phase5_approximate_risk_product
from riesgo_engelamiento.phase6 import build_phase6_heuristic_severity_product


def _build_final_product_dataset(include_pb: bool = False) -> xr.Dataset:
    time = np.array(
        ["2015-04-17T18:00:00", "2015-04-17T21:00:00"],
        dtype="datetime64[ns]",
    )
    bottom_top = 3
    south_north = 2
    west_east = 2
    bottom_top_stag = bottom_top + 1

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    qice = np.zeros_like(qcloud)
    theta = np.zeros_like(qcloud)
    pressure = np.zeros_like(qcloud)
    vertical = np.array([[1.0, 0.66, 0.33, 0.0], [1.0, 0.66, 0.33, 0.0]], dtype=np.float32)
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)

    qcloud[0, 2, 0, 0] = 1.0
    qrain[0, 2, 0, 0] = 1.0
    qice[0, 2, 0, 0] = 1.0

    qcloud[1, :, :, :] = 1.0
    qrain[1, :, :, :] = 1.0
    qice[1, :, :, :] = 1.0

    return xr.Dataset(
        data_vars={
            "QCLOUD": (EXPECTED_DIMS_BY_VARIABLE["QCLOUD"], qcloud),
            "QRAIN": (EXPECTED_DIMS_BY_VARIABLE["QRAIN"], qrain),
            "QICE": (EXPECTED_DIMS_BY_VARIABLE["QICE"], qice),
            "T": (EXPECTED_DIMS_BY_VARIABLE["T"], theta),
            "P": (EXPECTED_DIMS_BY_VARIABLE["P"], pressure),
            "ZNW": (EXPECTED_DIMS_BY_VARIABLE["ZNW"], vertical),
            "XLAT": (EXPECTED_DIMS_BY_VARIABLE["XLAT"], horizontal + 40.0),
            "XLONG": (EXPECTED_DIMS_BY_VARIABLE["XLONG"], horizontal - 3.0),
            **({"PB": (EXPECTED_DIMS_BY_VARIABLE["P"], pressure + 1.0)} if include_pb else {}),
        },
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def _build_highlighted_times_dataset(include_pb: bool = False) -> xr.Dataset:
    time = np.array(
        [
            "2015-04-17T18:00:00",
            "2015-04-17T19:00:00",
            "2015-04-17T20:00:00",
            "2015-04-17T21:00:00",
        ],
        dtype="datetime64[ns]",
    )
    bottom_top = 3
    south_north = 2
    west_east = 2
    bottom_top_stag = bottom_top + 1

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    qice = np.zeros_like(qcloud)
    theta = np.zeros_like(qcloud)
    pressure = np.zeros_like(qcloud)
    vertical = np.tile(np.array([1.0, 0.66, 0.33, 0.0], dtype=np.float32), (time.size, 1))
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)

    qcloud[0, 0, 0, 0] = 1.0
    qrain[0, 0, 0, 0] = 1.0
    qice[0, 0, 0, 0] = 1.0

    qcloud[1, 0:2, :, :] = 1.0
    qrain[1, 0:2, :, :] = 1.0
    qice[1, 0:2, :, :] = 1.0

    qcloud[2, :, :, :] = 1.0
    qrain[2, :, :, :] = 1.0
    qice[2, :, :, :] = 1.0

    qcloud[3, 0, :, :] = 1.0
    qrain[3, 0, :, :] = 1.0
    qice[3, 0, :, :] = 1.0

    return xr.Dataset(
        data_vars={
            "QCLOUD": (EXPECTED_DIMS_BY_VARIABLE["QCLOUD"], qcloud),
            "QRAIN": (EXPECTED_DIMS_BY_VARIABLE["QRAIN"], qrain),
            "QICE": (EXPECTED_DIMS_BY_VARIABLE["QICE"], qice),
            "T": (EXPECTED_DIMS_BY_VARIABLE["T"], theta),
            "P": (EXPECTED_DIMS_BY_VARIABLE["P"], pressure),
            "ZNW": (EXPECTED_DIMS_BY_VARIABLE["ZNW"], vertical),
            "XLAT": (EXPECTED_DIMS_BY_VARIABLE["XLAT"], horizontal + 40.0),
            "XLONG": (EXPECTED_DIMS_BY_VARIABLE["XLONG"], horizontal - 3.0),
            **({"PB": (EXPECTED_DIMS_BY_VARIABLE["P"], pressure + 1.0)} if include_pb else {}),
        },
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def _expected_auto_highlighted_indices(payload: dict[str, object], count: int) -> list[int]:
    metrics = payload["source_metrics"]  # type: ignore[index]
    severity = np.asarray(metrics["time_severity_score"], dtype=np.float32)  # type: ignore[index]
    persistence = np.asarray(metrics["time_persistence_fraction"], dtype=np.float32)  # type: ignore[index]
    risk = np.asarray(metrics["time_risk_horizontal_fraction"], dtype=np.float32)  # type: ignore[index]
    active = np.asarray(metrics["time_active_level_fraction"], dtype=np.float32)  # type: ignore[index]

    selected: list[int] = []
    seen: set[int] = set()
    for index in [int(np.argmax(severity)), int(np.argmax(persistence)), int(np.argmax(risk))]:
        if index in seen:
            continue
        selected.append(index)
        seen.add(index)
        if len(selected) >= count:
            return selected

    fallback = sorted(
        range(severity.shape[0]),
        key=lambda index: (
            float(severity[index]),
            float(persistence[index]),
            float(risk[index]),
            float(active[index]),
        ),
        reverse=True,
    )
    for index in fallback:
        if index in seen:
            continue
        selected.append(index)
        seen.add(index)
        if len(selected) >= count:
            break
    return selected


@pytest.mark.parametrize(
    ("include_pb", "expected_state", "expected_note"),
    [
        (True, "pb-present", "PB present"),
        (False, "pb-absent", "PB absent"),
    ],
)
def test_dataset_presentation_capabilities_distinguish_pb_presence(
    include_pb: bool,
    expected_state: str,
    expected_note: str,
) -> None:
    dataset = _build_final_product_dataset(include_pb=include_pb)
    capabilities = detect_dataset_presentation_capabilities(dataset)

    assert capabilities.has_pb is include_pb
    assert capabilities.presentation_state == expected_state
    assert capabilities.pb_state == ("present" if include_pb else "absent")
    assert expected_note in capabilities.figure_note
    if include_pb:
        assert "PB is present" in capabilities.report_note
    else:
        assert "PB is absent" in capabilities.report_note


def test_final_product_summary_tracks_inventory_contract_and_pb_capabilities() -> None:
    dataset = _build_final_product_dataset(include_pb=True)
    capabilities = detect_dataset_presentation_capabilities(dataset)
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    summary = build_final_product_summary(
        phase6_product,
        "synthetic.nc",
        render_view="heuristic-severity",
        selected_band="dominant",
        severity_product=phase6_product,
        presentation_capabilities=capabilities,
    )
    payload = summary.to_dict()
    markdown = summary.to_markdown()

    assert payload["presentation_inventory"]["artifact_label"] == "final-product"
    assert "title and subtitle" in payload["presentation_inventory"]["figure_copy"]
    assert payload["presentation_contract"]["artifact_label"] == "final-product"
    assert "full metric dumps" in payload["presentation_contract"]["figure_prohibited"]
    assert payload["presentation_capabilities"]["presentation_state"] == "pb-present"
    assert payload["presentation_capabilities"]["has_pb"] is True
    assert payload["figure_copy"]["title"] == "Final product map - heuristic-severity"
    assert payload["figure_copy"]["subtitle"] == "2015-04-17T18:00:00 | selected band lower vs dominant lower"
    assert payload["figure_copy"]["annotation_title"] == "Decision card"
    assert payload["figure_copy"]["annotation_lines"][-1] == "Caveat: PB present; proxy-only."
    assert payload["report_copy"]["presentation_summary"].startswith("Mode selected: heuristic-severity.")
    assert payload["report_copy"]["capability_note"] == "PB is present, so the report can point to a later thermodynamic refinement path."
    assert payload["trace_copy"]["presentation_inventory"]["artifact_label"] == "final-product"
    assert payload["trace_copy"]["presentation_contract"]["artifact_label"] == "final-product"
    assert payload["trace_copy"]["presentation_capabilities"]["presentation_state"] == "pb-present"
    assert "## Report copy" in markdown
    assert "### Capability note" in markdown
    assert "## Trace" in markdown
    assert "Decision card" not in markdown
    assert "Final product map - heuristic-severity" not in markdown
    assert "PB is present, so the report can point to a later thermodynamic refinement path." in markdown
    assert phase5_product.has_risk is True


def test_highlighted_times_summary_tracks_inventory_contract_and_pb_absence() -> None:
    dataset = _build_highlighted_times_dataset(include_pb=False)
    capabilities = detect_dataset_presentation_capabilities(dataset)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=1)
    summary = build_highlighted_times_summary(
        phase6_product,
        "synthetic.nc",
        source_mode="approximate-risk",
        highlighted_time_count=3,
        presentation_capabilities=capabilities,
    )
    payload = summary.to_dict()
    markdown = summary.to_markdown()

    assert payload["presentation_inventory"]["artifact_label"] == "highlighted-times"
    assert "temporal series plot" in payload["presentation_inventory"]["figure_copy"]
    assert payload["presentation_contract"]["artifact_label"] == "highlighted-times"
    assert "paragraph-style selection reasons" in payload["presentation_contract"]["figure_prohibited"]
    assert payload["presentation_capabilities"]["presentation_state"] == "pb-absent"
    assert payload["presentation_capabilities"]["has_pb"] is False
    assert payload["figure_copy"]["title"] == "Highlighted times - auto"
    assert payload["figure_copy"]["annotation_title"] == "Shortlist notes"
    assert payload["figure_copy"]["annotation_lines"][0] == "Reference: 19:00"
    assert len(payload["figure_copy"]["annotation_lines"]) == 4
    assert payload["figure_copy"]["annotation_lines"][1].startswith("#1 ")
    assert all("selected as" not in line for line in payload["figure_copy"]["annotation_lines"])
    assert payload["report_copy"]["selection_basis"].startswith("Auto-selection ranks")
    assert payload["report_copy"]["capability_note"] == "PB is absent, so the report must keep the approximate proxy caveat explicit."
    assert payload["trace_copy"]["highlighted_time_count"] == 3
    assert payload["trace_copy"]["presentation_inventory"]["artifact_label"] == "highlighted-times"
    assert payload["trace_copy"]["presentation_capabilities"]["presentation_state"] == "pb-absent"
    assert payload["source_metrics"]["time_display_labels"] == ["18:00", "19:00", "20:00", "21:00"]
    assert "## Report copy" in markdown
    assert "### Selection context" in markdown
    assert "### Highlighted times" in markdown
    assert "## Trace" in markdown
    assert "Shortlist notes" not in markdown
    assert "PB is absent, so the report must keep the approximate proxy caveat explicit." in markdown


def test_highlighted_times_figure_uses_compact_labels_and_short_notes() -> None:
    dataset = _build_highlighted_times_dataset()
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=1)
    summary = build_highlighted_times_summary(
        phase6_product,
        "synthetic.nc",
        source_mode="approximate-risk",
        highlighted_time_count=3,
    )

    figure = build_highlighted_times_figure(summary)
    try:
        assert len(figure.axes) == 3
        series_ax, compare_ax, notes_ax = figure.axes
        series_labels = [tick.get_text() for tick in series_ax.get_xticklabels()]
        compare_labels = [tick.get_text() for tick in compare_ax.get_xticklabels()]
        notes_text = "\n".join(text.get_text() for text in notes_ax.texts)

        assert series_labels == ["18:00", "19:00", "20:00", "21:00"]
        assert all("T" not in label for label in compare_labels)
        assert compare_labels[0].startswith("#1 ")
        assert "Shortlist notes" in notes_text
        assert "Reference:" in notes_text
        assert "Mode:" not in notes_text
        assert "selected as the maximum" not in notes_text
        assert "Rationale stays in Markdown and JSON." not in notes_text
    finally:
        plt.close(figure)


def test_final_product_summary_exports_traceable_risk_view(tmp_path: Path) -> None:
    dataset = _build_final_product_dataset()
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    summary = build_final_product_summary(
        phase5_product,
        "synthetic.nc",
        render_view="approximate-risk",
        selected_band="upper",
        severity_product=phase6_product,
        source_artifacts={
            "phase5_markdown": Path("phase5.md"),
            "phase5_json": Path("phase5.json"),
            "phase5_netcdf": Path("phase5.nc"),
            "phase5_png": Path("phase5.png"),
        },
    )
    markdown_path, json_path, png_path = write_final_product_outputs(
        summary,
        tmp_path,
        risk_product=phase5_product,
        source_dataset=dataset,
    )

    assert markdown_path.exists()
    assert json_path.exists()
    assert png_path.exists()
    assert markdown_path.name.startswith("presentation_final_deliverable_")
    assert json_path.name.startswith("presentation_final_deliverable_")
    assert png_path.name.startswith("presentation_final_deliverable_")
    assert "_band_upper" in markdown_path.name
    assert "_band_upper" in json_path.name
    assert "_band_upper" in png_path.name

    markdown_text = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Report copy" in markdown_text
    assert "### Presentation summary" in markdown_text
    assert "### Comparative summary" in markdown_text
    assert "### Aircraft-oriented interpretation" in markdown_text
    assert "### Capability note" in markdown_text
    assert "## Trace" in markdown_text
    assert "Artifact contract: `presentation/final-deliverable`" in markdown_text
    assert "Render view: `approximate-risk`" in markdown_text
    assert "Source phase: Phase 5" in markdown_text
    assert "Selected band request: upper" in markdown_text
    assert "Selected band: upper" in markdown_text
    assert "Selected band resolution: explicit" in markdown_text
    assert "Band relation: selected band upper differs from dominant band lower" in markdown_text
    assert "Delivery mode: entregable final canónico" in markdown_text
    assert "Approximate-risk is the binary Phase 5 proxy footprint" in markdown_text
    assert "not operational icing guidance" in markdown_text
    assert "phase5_markdown" in markdown_text
    assert "Decision card" not in markdown_text
    assert payload["artifact_kind"] == "presentation/final-deliverable"
    assert payload["output_purpose"] == "presentation/final-deliverable"
    assert payload["delivery_mode"] == "canonical"
    assert payload["delivery_label"] == "entregable final canónico"
    assert payload["source_mode"] == "approximate-risk"
    assert payload["render_view"] == "approximate-risk"
    assert payload["source_phase"] == 5
    assert payload["map_field_kind"] == "Phase 5 approximate-risk footprint (upper band)"
    assert payload["map_semantics"] == "binary approximate-risk footprint rendered directly from Phase 5 and conditioned on the selected upper model-relative band"
    assert "Cartopy PlateCarree map" in payload["map_geographic_context"]
    assert payload["selected_time_index"] == 0
    assert payload["selected_time_label"] == "2015-04-17T18:00:00"
    assert payload["selected_band_request"] == "upper"
    assert payload["selected_band"] == "upper"
    assert payload["selected_band_resolution"] == "explicit"
    assert payload["selected_band_eta_range"] == [0.66, 1.0]
    assert payload["selected_band_level_count"] == 1
    assert payload["selected_band_meaning"] == "Upper relative eta band of the model-level stack"
    assert payload["selected_band_signal_status"] == "empty"
    assert payload["dominant_band"] == "lower"
    assert payload["dominant_band_eta_range"] == [0.0, 0.33]
    assert payload["dominant_band_level_count"] == 1
    assert payload["dominant_band_meaning"] == "Lower relative eta band of the model-level stack"
    assert payload["band_relation"] == "selected band upper differs from dominant band lower"
    assert payload["contract"]["artifact_kind"] == "presentation/final-deliverable"
    assert payload["contract"]["output_prefix"] == "presentation_final_deliverable"
    assert payload["contract"]["delivery_mode"] == "canonical"
    assert payload["contract"]["delivery_label"] == "entregable final canónico"
    assert "selected_time_index" in payload["contract"]["required_metadata_fields"]
    assert "selected_time_label" in payload["contract"]["required_metadata_fields"]
    assert "delivery_mode" in payload["contract"]["required_metadata_fields"]
    assert "delivery_label" in payload["contract"]["required_metadata_fields"]
    assert "selected_band_request" in payload["contract"]["required_metadata_fields"]
    assert "selected_band" in payload["contract"]["required_metadata_fields"]
    assert "selected_band_resolution" in payload["contract"]["required_metadata_fields"]
    assert "dominant_band" in payload["contract"]["required_metadata_fields"]
    assert "band_relation" in payload["contract"]["required_metadata_fields"]
    assert "presentation_summary" in payload["contract"]["required_metadata_fields"]
    assert "comparative_summary" in payload["contract"]["required_metadata_fields"]
    assert "aircraft_interpretation" in payload["contract"]["required_metadata_fields"]
    assert "map_field_kind" in payload["contract"]["required_metadata_fields"]
    assert "map_semantics" in payload["contract"]["required_metadata_fields"]
    assert "map_geographic_context" in payload["contract"]["required_metadata_fields"]
    assert "outputs" in payload["contract"]["required_metadata_fields"]
    assert payload["contract"]["supported_views"] == ["approximate-risk", "heuristic-severity"]
    assert payload["report_copy"]["presentation_summary"].startswith("Mode selected: approximate-risk.")
    assert payload["trace_copy"]["presentation_inventory"]["artifact_label"] == "final-product"
    assert payload["presentation_summary"].startswith("Mode selected: approximate-risk.")
    assert "Delivery mode: entregable final canónico" in payload["presentation_summary"]
    assert "Rendered band: upper" in payload["presentation_summary"]
    assert "selected-band risk" in payload["presentation_summary"]
    assert "heuristic-severity" in payload["comparative_summary"]
    assert "binary Phase 5 proxy footprint" in payload["comparative_summary"]
    assert "not a flight level" in payload["aircraft_interpretation"]
    assert payload["source_metrics"]["has_risk"] is True
    assert payload["source_metrics"]["selected_band_signal_status"] == "empty"
    assert "map_geographic_context" in payload


def test_final_product_figure_contains_self_contained_annotations() -> None:
    dataset = _build_final_product_dataset()
    capabilities = detect_dataset_presentation_capabilities(dataset)
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    summary = build_final_product_summary(
        phase6_product,
        "synthetic.nc",
        render_view="heuristic-severity",
        selected_band="dominant",
        severity_product=phase6_product,
        presentation_capabilities=capabilities,
        source_artifacts={
            "phase5_markdown": Path("phase5.md"),
            "phase5_json": Path("phase5.json"),
            "phase5_netcdf": Path("phase5.nc"),
            "phase5_png": Path("phase5.png"),
            "phase6_markdown": Path("phase6.md"),
            "phase6_json": Path("phase6.json"),
            "phase6_netcdf": Path("phase6.nc"),
            "phase6_png": Path("phase6.png"),
        },
    )

    figure = build_final_product_figure(summary, phase5_product, phase6_product, dataset)
    try:
        assert len(figure.axes) == 3
        map_axis, annotation_axis, colorbar_axis = figure.axes
        assert type(map_axis.projection).__name__ == "PlateCarree"
        assert map_axis.get_position().width > annotation_axis.get_position().width
        feature_artists = [collection for collection in map_axis.collections if collection.__class__.__module__.startswith("cartopy.mpl.feature_artist")]
        assert len(feature_artists) >= 3
        extent = map_axis.get_extent(crs=ccrs.PlateCarree())
        assert extent[0] < extent[1]
        assert extent[2] < extent[3]
        assert extent[0] < -3.0 < extent[1]
        assert extent[2] < 40.0 < extent[3]
        annotation_text = "\n".join(text.get_text() for text in annotation_axis.texts)
        assert "Decision card" in annotation_text
        assert "Time: 2015-04-17T18:00:00" in annotation_text
        assert "Band: lower vs dominant lower" in annotation_text
        assert "Severity: moderate" in annotation_text
        assert "Caveat: PB absent; proxy-only." in annotation_text
        assert "Presentation summary:" not in annotation_text
        assert "Comparative summary:" not in annotation_text
        assert "Band score formula" not in annotation_text
        assert map_axis.get_legend() is None
        assert map_axis.get_title(loc="left") == "Final product map - heuristic-severity"
        assert colorbar_axis.get_ylabel() == "Band-conditioned heuristic severity score (0-100)"
    finally:
        plt.close(figure)


def test_final_product_figure_approximate_risk_preserves_short_copy_and_hierarchy() -> None:
    dataset = _build_final_product_dataset(include_pb=True)
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    capabilities = detect_dataset_presentation_capabilities(dataset)
    summary = build_final_product_summary(
        phase5_product,
        "synthetic.nc",
        render_view="approximate-risk",
        selected_band="upper",
        severity_product=phase6_product,
        presentation_capabilities=capabilities,
    )

    figure = build_final_product_figure(summary, phase5_product, phase6_product, dataset)
    try:
        assert len(figure.axes) == 2
        map_axis, annotation_axis = figure.axes
        assert map_axis.get_position().width > annotation_axis.get_position().width
        annotation_text = "\n".join(text.get_text() for text in annotation_axis.texts)
        assert "Decision card" in annotation_text
        assert "Coverage:" in annotation_text
        assert "Caveat: PB present; proxy-only." in annotation_text
        assert "Presentation summary:" not in annotation_text
        assert map_axis.get_title(loc="left") == "Final product map - approximate-risk"
    finally:
        plt.close(figure)


def test_main_writes_canonical_final_deliverable_artifacts_when_requested(tmp_path: Path, monkeypatch) -> None:
    dataset = _build_final_product_dataset()
    dataset_file = tmp_path / "dummy.nc"
    dataset_file.write_text("placeholder", encoding="utf-8")
    output_dir = tmp_path / "outputs"

    class _DatasetContext:
        def __init__(self, wrapped: xr.Dataset) -> None:
            self._wrapped = wrapped

        def __enter__(self) -> xr.Dataset:
            return self._wrapped

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(cli, "open_dataset", lambda path: _DatasetContext(dataset))

    exit_code = cli.main(
        [
            "--dataset",
            str(dataset_file),
            "--output-dir",
            str(output_dir),
            "--time-index",
            "0",
            "--final-deliverable",
            "--final-product-band",
            "upper",
        ]
    )

    assert exit_code == 0
    final_markdown = sorted(output_dir.glob("presentation_final_deliverable_*.md"))
    final_json = sorted(output_dir.glob("presentation_final_deliverable_*.json"))
    final_png = sorted(output_dir.glob("presentation_final_deliverable_*.png"))

    assert len(final_markdown) == 1
    assert len(final_json) == 1
    assert len(final_png) == 1
    assert "_band_upper" in final_markdown[0].name
    assert "_band_upper" in final_json[0].name
    assert "_band_upper" in final_png[0].name

    final_markdown_text = final_markdown[0].read_text(encoding="utf-8")
    final_payload = json.loads(final_json[0].read_text(encoding="utf-8"))

    assert "Artifact contract: `presentation/final-deliverable`" in final_markdown_text
    assert "Delivery mode: `canonical`" in final_markdown_text
    assert "Delivery label: entregable final canónico" in final_markdown_text
    assert "Mode selected: heuristic-severity." in final_payload["presentation_summary"]
    assert final_payload["artifact_kind"] == "presentation/final-deliverable"
    assert final_payload["output_purpose"] == "presentation/final-deliverable"
    assert final_payload["delivery_mode"] == "canonical"
    assert final_payload["delivery_label"] == "entregable final canónico"
    assert final_payload["contract"]["output_prefix"] == "presentation_final_deliverable"
    assert final_payload["contract"]["artifact_kind"] == "presentation/final-deliverable"
    assert final_payload["selected_band_request"] == "upper"
    assert final_payload["selected_band"] == "upper"
    assert final_payload["selected_band_resolution"] == "explicit"


def test_main_writes_final_product_artifacts_when_requested(tmp_path: Path, monkeypatch) -> None:
    dataset = _build_final_product_dataset()
    dataset_file = tmp_path / "dummy.nc"
    dataset_file.write_text("placeholder", encoding="utf-8")
    output_dir = tmp_path / "outputs"

    class _DatasetContext:
        def __init__(self, wrapped: xr.Dataset) -> None:
            self._wrapped = wrapped

        def __enter__(self) -> xr.Dataset:
            return self._wrapped

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(cli, "open_dataset", lambda path: _DatasetContext(dataset))

    exit_code = cli.main(
        [
            "--dataset",
            str(dataset_file),
            "--output-dir",
            str(output_dir),
            "--time-index",
            "0",
            "--final-product",
            "--final-product-band",
            "upper",
        ]
    )

    assert exit_code == 0
    final_markdown = sorted(output_dir.glob("presentation_final_product_*.md"))
    final_json = sorted(output_dir.glob("presentation_final_product_*.json"))
    final_png = sorted(output_dir.glob("presentation_final_product_*.png"))
    phase2_markdown = sorted(output_dir.glob("phase2_liquid_presence_*.md"))
    phase5_markdown = sorted(output_dir.glob("phase5_approximate_icing_risk_*.md"))
    phase6_markdown = sorted(output_dir.glob("phase6_heuristic_severity_*.md"))

    assert len(final_markdown) == 1
    assert len(final_json) == 1
    assert len(final_png) == 1
    assert "_band_upper" in final_markdown[0].name
    assert "_band_upper" in final_json[0].name
    assert "_band_upper" in final_png[0].name
    assert len(phase2_markdown) == 1
    assert len(phase5_markdown) == 1
    assert len(phase6_markdown) == 1

    final_markdown_text = final_markdown[0].read_text(encoding="utf-8")
    final_payload = json.loads(final_json[0].read_text(encoding="utf-8"))

    assert "## Report copy" in final_markdown_text
    assert "### Presentation summary" in final_markdown_text
    assert "### Comparative summary" in final_markdown_text
    assert "### Aircraft-oriented interpretation" in final_markdown_text
    assert "Artifact contract: `presentation/final-product`" in final_markdown_text
    assert "Delivery mode: `legacy`" in final_markdown_text
    assert "Delivery label: producto final heredado" in final_markdown_text
    assert "Render view: `heuristic-severity`" in final_markdown_text
    assert "Source phase: Phase 6" in final_markdown_text
    assert "Selected band request: upper" in final_markdown_text
    assert "Selected band: upper" in final_markdown_text
    assert "Selected band signal status: empty" in final_markdown_text
    assert "## Trace" in final_markdown_text
    assert "phase6_markdown" in final_markdown_text
    assert "Cartopy PlateCarree map" in final_markdown_text
    assert "png" in final_markdown_text
    assert final_payload["render_view"] == "heuristic-severity"
    assert final_payload["source_mode"] == "heuristic-severity"
    assert final_payload["source_phase"] == 6
    assert final_payload["artifact_kind"] == "presentation/final-product"
    assert final_payload["output_purpose"] == "presentation/final-product"
    assert final_payload["delivery_mode"] == "legacy"
    assert final_payload["delivery_label"] == "producto final heredado"
    assert final_payload["map_field_kind"] == "Spatial heuristic severity score (upper band)"
    assert "band-conditioned" in final_payload["map_semantics"]
    assert "Cartopy PlateCarree map" in final_payload["map_geographic_context"]
    assert final_payload["selected_band_request"] == "upper"
    assert final_payload["selected_band"] == "upper"
    assert final_payload["selected_band_resolution"] == "explicit"
    assert final_payload["selected_band_signal_status"] == "empty"
    assert final_payload["dominant_band"] == "lower"
    assert final_payload["presentation_summary"].startswith("Mode selected: heuristic-severity.")
    assert "Delivery mode: producto final heredado" in final_payload["presentation_summary"]
    assert "severity moderate" in final_payload["presentation_summary"]
    assert final_payload["report_copy"]["capability_note"].startswith("PB state unknown")
    assert final_payload["trace_copy"]["presentation_inventory"]["artifact_label"] == "final-product"
    assert "Heuristic-severity adds a graded, band-conditioned score" in final_payload["comparative_summary"]
    assert "not operational icing guidance" in final_payload["aircraft_interpretation"]
    assert final_payload["contract"]["output_prefix"] == "presentation_final_product"
    assert "map_geographic_context" in final_payload["contract"]["required_metadata_fields"]
    assert "presentation_summary" in final_payload["contract"]["required_metadata_fields"]
    assert "comparative_summary" in final_payload["contract"]["required_metadata_fields"]
    assert "aircraft_interpretation" in final_payload["contract"]["required_metadata_fields"]
    assert final_payload["selected_time_index"] == 0
    assert final_payload["selected_time_label"] == "2015-04-17T18:00:00"
    assert final_payload["source_metrics"]["severity_class"] == "moderate"
    assert final_payload["outputs"]["png"].endswith(".png")


def test_highlighted_times_summary_explicit_selection_exports_traceable_metadata(tmp_path: Path) -> None:
    dataset = _build_highlighted_times_dataset()
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=1)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=1)
    summary = build_highlighted_times_summary(
        phase6_product,
        "synthetic.nc",
        source_mode="heuristic-severity",
        highlighted_times=[3, 1, 3, -1],
        source_artifacts={
            "phase5_markdown": Path("phase5.md"),
            "phase5_json": Path("phase5.json"),
            "phase5_netcdf": Path("phase5.nc"),
            "phase5_png": Path("phase5.png"),
            "phase6_markdown": Path("phase6.md"),
            "phase6_json": Path("phase6.json"),
            "phase6_netcdf": Path("phase6.nc"),
            "phase6_png": Path("phase6.png"),
        },
    )
    markdown_path, json_path, png_path = write_highlighted_times_outputs(summary, tmp_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert png_path.exists()
    assert "_explicit_t003_t001" in markdown_path.name
    assert "_explicit_t003_t001" in json_path.name
    assert "_explicit_t003_t001" in png_path.name

    markdown_text = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Highlighted times" in markdown_text
    assert "Selection mode: explicit" in markdown_text
    assert "selected from the user-requested highlighted-time list" in markdown_text
    assert "Reference time index: 1" in markdown_text
    assert payload["artifact_kind"] == "presentation/final-product/highlighted-times"
    assert payload["comparison_mode"] == "highlighted-times"
    assert payload["source_mode"] == "heuristic-severity"
    assert payload["reference_time_index"] == 1
    assert payload["reference_time_label"] == "2015-04-17T19:00:00"
    assert payload["selection_mode"] == "explicit"
    assert payload["highlighted_time_count"] == 2
    assert payload["highlighted_time_indices"] == [3, 1]
    assert payload["highlighted_time_labels"] == ["2015-04-17T21:00:00", "2015-04-17T19:00:00"]
    assert payload["highlighted_time_reasons"] == [
        "selected from the user-requested highlighted-time list",
        "selected from the user-requested highlighted-time list",
    ]
    assert len(payload["highlighted_times"]) == 2
    assert payload["report_copy"]["selection_basis"].startswith("User-requested highlighted times")
    assert payload["trace_copy"]["highlighted_time_count"] == 2
    assert payload["figure_copy"]["title"] == "Highlighted times - explicit"
    assert len(payload["figure_copy"]["annotation_lines"]) == 3
    assert all("selected from" not in line for line in payload["figure_copy"]["annotation_lines"])
    assert payload["highlighted_times"][0]["selection_rule"] == "explicit-request"
    assert "highlighted_times" in payload["contract"]["required_metadata_fields"]
    assert "selection_mode" in payload["contract"]["required_metadata_fields"]
    assert "comparison_mode" in payload["contract"]["required_metadata_fields"]
    assert payload["contract"]["selection_modes"] == ["explicit", "auto"]
    assert payload["contract"]["output_prefix"] == "presentation_final_product_highlighted_times"
    assert payload["outputs"]["png"].endswith(".png")
    assert payload["source_metrics"]["selection_mode"] == "explicit"
    assert payload["source_metrics"]["selection_basis"].startswith("User-requested highlighted times")
    assert "## Report copy" in markdown_text
    assert "### Selection context" in markdown_text
    assert "### Highlighted times" in markdown_text
    assert "## Trace" in markdown_text


def test_highlighted_times_summary_auto_selection_is_reproducible(tmp_path: Path) -> None:
    dataset = _build_highlighted_times_dataset()
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=1)
    summary = build_highlighted_times_summary(
        phase6_product,
        "synthetic.nc",
        source_mode="approximate-risk",
        highlighted_time_count=3,
        source_artifacts={
            "phase5_markdown": Path("phase5.md"),
            "phase5_json": Path("phase5.json"),
            "phase5_netcdf": Path("phase5.nc"),
            "phase5_png": Path("phase5.png"),
            "phase6_markdown": Path("phase6.md"),
            "phase6_json": Path("phase6.json"),
            "phase6_netcdf": Path("phase6.nc"),
            "phase6_png": Path("phase6.png"),
        },
    )
    markdown_path, json_path, png_path = write_highlighted_times_outputs(summary, tmp_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert png_path.exists()

    markdown_text = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "Selection mode: auto" in markdown_text
    assert "severity peak" in markdown_text or "maximum heuristic-severity score" in markdown_text
    assert payload["selection_mode"] == "auto"
    assert payload["highlighted_time_count"] == 3
    assert payload["report_copy"]["selection_basis"].startswith("Auto-selection ranks")
    assert payload["trace_copy"]["highlighted_time_count"] == 3
    assert payload["highlighted_time_indices"] == _expected_auto_highlighted_indices(payload, 3)
    assert len(payload["highlighted_times"]) == 3
    assert payload["highlighted_times"][0]["rank"] == 1
    assert payload["highlighted_times"][0]["selection_rule"] in {"max-severity", "max-persistence", "max-risk-coverage"}
    assert payload["figure_copy"]["annotation_title"] == "Shortlist notes"
    assert payload["source_metrics"]["reference_time_display_label"] == "19:00"
    assert len(payload["figure_copy"]["annotation_lines"]) == 4
    assert payload["contract"]["artifact_kind"] == "presentation/final-product/highlighted-times"
    assert "highlighted_time_indices" in payload["contract"]["required_metadata_fields"]
    assert "highlighted_times" in payload["contract"]["required_metadata_fields"]
    assert "comparison_mode" in payload["contract"]["required_metadata_fields"]
    assert payload["source_metrics"]["peak_severity_time_index"] == int(np.argmax(np.asarray(payload["source_metrics"]["time_severity_score"], dtype=np.float32)))
    assert payload["source_metrics"]["selection_mode"] == "auto"
    assert "## Report copy" in markdown_text
    assert "### Selection context" in markdown_text
    assert "### Highlighted times" in markdown_text


def test_main_writes_highlighted_times_artifacts_when_requested(tmp_path: Path, monkeypatch) -> None:
    dataset = _build_highlighted_times_dataset()
    dataset_file = tmp_path / "dummy.nc"
    dataset_file.write_text("placeholder", encoding="utf-8")
    output_dir = tmp_path / "outputs"

    class _DatasetContext:
        def __init__(self, wrapped: xr.Dataset) -> None:
            self._wrapped = wrapped

        def __enter__(self) -> xr.Dataset:
            return self._wrapped

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(cli, "open_dataset", lambda path: _DatasetContext(dataset))

    exit_code = cli.main(
        [
            "--dataset",
            str(dataset_file),
            "--output-dir",
            str(output_dir),
            "--time-index",
            "1",
            "--final-product",
            "--final-product-highlighted-count",
            "3",
        ]
    )

    assert exit_code == 0
    final_markdown = [
        path
        for path in sorted(output_dir.glob("presentation_final_product_*.md"))
        if not path.name.startswith("presentation_final_product_highlighted_times_")
    ]
    highlighted_markdown = sorted(output_dir.glob("presentation_final_product_highlighted_times_*.md"))
    highlighted_json = sorted(output_dir.glob("presentation_final_product_highlighted_times_*.json"))
    highlighted_png = sorted(output_dir.glob("presentation_final_product_highlighted_times_*.png"))

    assert len(final_markdown) == 1
    assert len(highlighted_markdown) == 1
    assert len(highlighted_json) == 1
    assert len(highlighted_png) == 1

    highlighted_markdown_text = highlighted_markdown[0].read_text(encoding="utf-8")
    highlighted_payload = json.loads(highlighted_json[0].read_text(encoding="utf-8"))

    assert "Selection mode: auto" in highlighted_markdown_text
    assert "## Report copy" in highlighted_markdown_text
    assert "### Selection context" in highlighted_markdown_text
    assert "### Highlighted times" in highlighted_markdown_text
    assert highlighted_payload["comparison_mode"] == "highlighted-times"
    assert highlighted_payload["selection_mode"] == "auto"
    assert highlighted_payload["highlighted_time_count"] == 3
    assert highlighted_payload["trace_copy"]["highlighted_time_count"] == 3
    assert highlighted_payload["outputs"]["png"].endswith(".png")
