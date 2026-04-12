from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import xarray as xr

from riesgo_engelamiento import cli
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.final_product import (
    build_final_product_figure,
    build_final_product_summary,
    write_final_product_outputs,
)
from riesgo_engelamiento.phase5 import build_phase5_approximate_risk_product
from riesgo_engelamiento.phase6 import build_phase6_heuristic_severity_product


def _build_final_product_dataset() -> xr.Dataset:
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
        },
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def test_final_product_summary_exports_traceable_risk_view(tmp_path: Path) -> None:
    dataset = _build_final_product_dataset()
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    summary = build_final_product_summary(
        phase5_product,
        "synthetic.nc",
        render_view="approximate-risk",
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

    markdown_text = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "Artifact contract: `presentation/final-product`" in markdown_text
    assert "Render view: `approximate-risk`" in markdown_text
    assert "Source phase: Phase 5" in markdown_text
    assert "phase5_markdown" in markdown_text
    assert payload["artifact_kind"] == "presentation/final-product"
    assert payload["source_mode"] == "approximate-risk"
    assert payload["render_view"] == "approximate-risk"
    assert payload["source_phase"] == 5
    assert payload["map_field_kind"] == "Phase 5 approximate-risk footprint"
    assert payload["map_semantics"] == "binary approximate-risk footprint rendered directly from Phase 5"
    assert "Cartopy PlateCarree map" in payload["map_geographic_context"]
    assert payload["selected_time_index"] == 0
    assert payload["selected_time_label"] == "2015-04-17T18:00:00"
    assert "selected_time_index" in payload["contract"]["required_metadata_fields"]
    assert "selected_time_label" in payload["contract"]["required_metadata_fields"]
    assert "map_field_kind" in payload["contract"]["required_metadata_fields"]
    assert "map_semantics" in payload["contract"]["required_metadata_fields"]
    assert "map_geographic_context" in payload["contract"]["required_metadata_fields"]
    assert "outputs" in payload["contract"]["required_metadata_fields"]
    assert payload["contract"]["supported_views"] == ["approximate-risk", "heuristic-severity"]
    assert payload["source_metrics"]["has_risk"] is True
    assert "map_geographic_context" in payload


def test_final_product_figure_contains_self_contained_annotations() -> None:
    dataset = _build_final_product_dataset()
    phase5_product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    phase6_product = build_phase6_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    summary = build_final_product_summary(
        phase6_product,
        "synthetic.nc",
        render_view="heuristic-severity",
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
        feature_artists = [collection for collection in map_axis.collections if collection.__class__.__module__.startswith("cartopy.mpl.feature_artist")]
        assert len(feature_artists) >= 3
        extent = map_axis.get_extent(crs=ccrs.PlateCarree())
        assert extent[0] < extent[1]
        assert extent[2] < extent[3]
        assert extent[0] < -3.0 < extent[1]
        assert extent[2] < 40.0 < extent[3]
        annotation_text = "\n".join(text.get_text() for text in annotation_axis.texts)
        assert "Final product annotations" in annotation_text
        assert "heuristic-severity" in annotation_text
        assert "Severity class" in annotation_text
        assert "Dominant band" in annotation_text
        assert "Spatial score range" in annotation_text
        assert "Spatial score formula" in annotation_text
        assert "Caveats" in annotation_text
        assert map_axis.get_legend() is None
        assert "spatial heuristic severity score" in map_axis.get_title(loc="left")
        assert colorbar_axis.get_ylabel() == "Spatial heuristic severity score (0-100)"
    finally:
        plt.close(figure)


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
    assert len(phase2_markdown) == 1
    assert len(phase5_markdown) == 1
    assert len(phase6_markdown) == 1

    final_markdown_text = final_markdown[0].read_text(encoding="utf-8")
    final_payload = json.loads(final_json[0].read_text(encoding="utf-8"))

    assert "Artifact contract: `presentation/final-product`" in final_markdown_text
    assert "Render view: `heuristic-severity`" in final_markdown_text
    assert "Source phase: Phase 6" in final_markdown_text
    assert "phase6_markdown" in final_markdown_text
    assert "Cartopy PlateCarree map" in final_markdown_text
    assert "png" in final_markdown_text
    assert final_payload["render_view"] == "heuristic-severity"
    assert final_payload["source_mode"] == "heuristic-severity"
    assert final_payload["source_phase"] == 6
    assert final_payload["map_field_kind"] == "Spatial heuristic severity score"
    assert "2D heuristic severity score" in final_payload["map_semantics"]
    assert "Cartopy PlateCarree map" in final_payload["map_geographic_context"]
    assert "map_geographic_context" in final_payload["contract"]["required_metadata_fields"]
    assert final_payload["selected_time_index"] == 0
    assert final_payload["selected_time_label"] == "2015-04-17T18:00:00"
    assert final_payload["source_metrics"]["severity_class"] == "moderate"
    assert final_payload["outputs"]["png"].endswith(".png")
