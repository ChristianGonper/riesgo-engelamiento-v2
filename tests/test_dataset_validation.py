from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from riesgo_engelamiento import cli
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.final_product import detect_dataset_presentation_capabilities
from riesgo_engelamiento.dataset import DatasetValidationError, assert_valid, validate_dataset
from riesgo_engelamiento.phase2 import build_phase2_liquid_product
from riesgo_engelamiento.summary import build_phase1_summary


def _build_dataset(
    include_qrain: bool = True,
    include_bottom_top_stag: bool = True,
    include_pb: bool = False,
) -> xr.Dataset:
    time = np.array(
        ["2015-04-17T18:00:00", "2015-04-17T21:00:00"],
        dtype="datetime64[ns]",
    )
    bottom_top = 3
    south_north = 4
    west_east = 5
    bottom_top_stag = bottom_top + 1

    field = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    vertical = np.zeros((time.size, bottom_top_stag), dtype=np.float32)
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)

    data_vars = {
        "QCLOUD": (EXPECTED_DIMS_BY_VARIABLE["QCLOUD"], field.copy()),
        "QICE": (EXPECTED_DIMS_BY_VARIABLE["QICE"], field.copy()),
        "T": (EXPECTED_DIMS_BY_VARIABLE["T"], field.copy()),
        "P": (EXPECTED_DIMS_BY_VARIABLE["P"], field.copy()),
        "XLAT": (EXPECTED_DIMS_BY_VARIABLE["XLAT"], horizontal.copy()),
        "XLONG": (EXPECTED_DIMS_BY_VARIABLE["XLONG"], horizontal.copy()),
    }
    if include_qrain:
        data_vars["QRAIN"] = (EXPECTED_DIMS_BY_VARIABLE["QRAIN"], field.copy())
    if include_bottom_top_stag:
        data_vars["ZNW"] = (EXPECTED_DIMS_BY_VARIABLE["ZNW"], vertical.copy())
    if include_pb:
        data_vars["PB"] = (EXPECTED_DIMS_BY_VARIABLE["P"], field.copy())

    return xr.Dataset(
        data_vars=data_vars,
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def _build_phase2_dataset(
    qcloud_cells: tuple[tuple[int, int, int], ...] = (),
    qrain_cells: tuple[tuple[int, int, int], ...] = (),
) -> xr.Dataset:
    time = np.array(["2015-04-17T18:00:00"], dtype="datetime64[ns]")
    bottom_top = 2
    south_north = 2
    west_east = 3
    bottom_top_stag = bottom_top + 1

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    qice = np.zeros_like(qcloud)
    theta = np.zeros_like(qcloud)
    pressure = np.zeros_like(qcloud)
    vertical = np.zeros((time.size, bottom_top_stag), dtype=np.float32)
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)

    for level, north, east in qcloud_cells:
        qcloud[0, level, north, east] = 1.0
    for level, north, east in qrain_cells:
        qrain[0, level, north, east] = 1.0

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


def test_validate_dataset_accepts_complete_dataset() -> None:
    dataset = _build_dataset()
    report = validate_dataset(dataset, source="synthetic.nc")

    assert report.is_valid
    assert report.missing_variables == ()
    assert report.missing_dimensions == ()
    assert "PB is absent" in report.warnings[0]

    summary = build_phase1_summary(dataset, report, "synthetic.nc")
    assert summary.time_count == 2
    assert summary.horizontal_shape == (4, 5)
    assert summary.vertical_levels == 3
    assert summary.vertical_staggered_levels == 4
    assert "available with caveats" in summary.to_markdown()
    assert "T0 = 300 K" in summary.to_markdown()
    diagnostics = {diagnostic.name: diagnostic for diagnostic in summary.diagnostics}
    assert diagnostics["Phase 6 heuristic severity"].status == "available with caveats"


def test_validate_dataset_and_phase1_summary_adjust_pb_notes_when_pb_is_present() -> None:
    dataset = _build_dataset(include_pb=True)
    report = validate_dataset(dataset, source="synthetic.nc")
    summary = build_phase1_summary(dataset, report, "synthetic.nc")
    markdown = summary.to_markdown()

    assert report.is_valid
    assert report.warnings == ()
    diagnostics = {diagnostic.name: diagnostic for diagnostic in summary.diagnostics}
    assert diagnostics["Approximate icing risk"].reason.startswith("PB is present")
    assert "PB is present, but the current phase-5 proxy still uses the documented approximate path" in markdown
    assert "PB is absent, so exact pressure and exact temperature reconstruction are not possible" not in markdown


@pytest.mark.parametrize(
    ("include_pb", "expected_state"),
    [
        (True, "pb-present"),
        (False, "pb-absent"),
    ],
)
def test_dataset_presentation_capabilities_track_pb_presence(
    include_pb: bool,
    expected_state: str,
) -> None:
    dataset = _build_dataset(include_pb=include_pb)
    capabilities = detect_dataset_presentation_capabilities(dataset)

    assert capabilities.has_pb is include_pb
    assert capabilities.presentation_state == expected_state
    assert capabilities.pb_state == ("present" if include_pb else "absent")
    if include_pb:
        assert capabilities.report_note.startswith("PB is present")
    else:
        assert capabilities.report_note.startswith("PB is absent")


def test_validate_dataset_reports_missing_inputs_and_raises_on_request() -> None:
    dataset = _build_dataset(include_qrain=False, include_bottom_top_stag=False)
    report = validate_dataset(dataset, source="synthetic.nc")

    assert not report.is_valid
    assert "QRAIN" in report.error_message()
    assert "bottom_top_stag" in report.error_message()

    with pytest.raises(DatasetValidationError):
        assert_valid(report)


def test_main_writes_artifacts_even_when_validation_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _build_dataset(include_qrain=False, include_bottom_top_stag=False)
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

    exit_code = cli.main(["--dataset", str(dataset_file), "--output-dir", str(output_dir)])

    assert exit_code == 1
    markdown_path = output_dir / "phase1_summary.md"
    json_path = output_dir / "phase1_summary.json"
    assert markdown_path.exists()
    assert json_path.exists()
    assert "invalid" in markdown_path.read_text(encoding="utf-8")
    assert not any(output_dir.glob("phase2_liquid_presence_*.md"))
    assert not any(output_dir.glob("phase2_liquid_presence_*.json"))
    assert not any(output_dir.glob("phase2_liquid_presence_*.nc"))
    assert not any(output_dir.glob("phase2_liquid_presence_*.png"))
    assert not any(output_dir.glob("phase5_approximate_icing_risk_*.md"))
    assert not any(output_dir.glob("phase5_approximate_icing_risk_*.json"))
    assert not any(output_dir.glob("phase5_approximate_icing_risk_*.nc"))
    assert not any(output_dir.glob("phase5_approximate_icing_risk_*.png"))
    assert not any(output_dir.glob("phase6_heuristic_severity_*.md"))
    assert not any(output_dir.glob("phase6_heuristic_severity_*.json"))
    assert not any(output_dir.glob("phase6_heuristic_severity_*.nc"))
    assert not any(output_dir.glob("phase6_heuristic_severity_*.png"))


def test_invalid_summary_does_not_claim_missing_diagnostics_are_supported() -> None:
    dataset = _build_dataset(include_qrain=False, include_bottom_top_stag=False)
    report = validate_dataset(dataset, source="synthetic.nc")
    summary = build_phase1_summary(dataset, report, "synthetic.nc")

    diagnostics = {diagnostic.name: diagnostic for diagnostic in summary.diagnostics}
    assert diagnostics["Liquid-water presence"].status == "unsupported"
    assert "QRAIN" in diagnostics["Liquid-water presence"].reason
    assert diagnostics["Vertical structure"].status == "unsupported"
    assert "bottom_top_stag" in report.missing_dimensions
    assert diagnostics["Approximate icing risk"].status == "unsupported"
    assert "ZNW" in diagnostics["Approximate icing risk"].reason
    assert diagnostics["Phase 6 heuristic severity"].status == "unsupported"
    assert "QRAIN" in diagnostics["Phase 6 heuristic severity"].reason
    assert "ZNW" in diagnostics["Phase 6 heuristic severity"].reason


@pytest.mark.parametrize(
    ("qcloud_cells", "qrain_cells", "expected_count", "expected_has_liquid"),
    [
        (((0, 0, 0),), (), 1, True),
        ((), ((1, 0, 1),), 1, True),
        (((0, 0, 0),), ((1, 0, 1),), 2, True),
        ((), (), 0, False),
    ],
)
def test_phase2_liquid_product_counts_qcloud_qrain_and_empty_cases(
    qcloud_cells: tuple[tuple[int, int, int], ...],
    qrain_cells: tuple[tuple[int, int, int], ...],
    expected_count: int,
    expected_has_liquid: bool,
) -> None:
    dataset = _build_phase2_dataset(qcloud_cells=qcloud_cells, qrain_cells=qrain_cells)
    product = build_phase2_liquid_product(dataset, "synthetic.nc", time_index=0)

    assert product.liquid_cell_count == expected_count
    assert product.has_liquid is expected_has_liquid
    assert product.total_cell_count == 6
    if expected_has_liquid:
        assert "present" in product.to_markdown()
    else:
        assert "No liquid hydrometeors were detected" in product.to_markdown()


def test_main_writes_phase2_artifacts_for_selected_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _build_phase2_dataset(qcloud_cells=((0, 0, 0),), qrain_cells=((1, 1, 2),))
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

    exit_code = cli.main(["--dataset", str(dataset_file), "--output-dir", str(output_dir), "--time-index", "0"])

    assert exit_code == 0
    phase2_markdown = sorted(output_dir.glob("phase2_liquid_presence_*.md"))
    phase2_json = sorted(output_dir.glob("phase2_liquid_presence_*.json"))
    phase2_netcdf = sorted(output_dir.glob("phase2_liquid_presence_*.nc"))
    phase2_png = sorted(output_dir.glob("phase2_liquid_presence_*.png"))
    phase5_markdown = sorted(output_dir.glob("phase5_approximate_icing_risk_*.md"))
    phase5_json = sorted(output_dir.glob("phase5_approximate_icing_risk_*.json"))
    phase5_netcdf = sorted(output_dir.glob("phase5_approximate_icing_risk_*.nc"))
    phase5_png = sorted(output_dir.glob("phase5_approximate_icing_risk_*.png"))
    phase6_markdown = sorted(output_dir.glob("phase6_heuristic_severity_*.md"))
    phase6_json = sorted(output_dir.glob("phase6_heuristic_severity_*.json"))
    phase6_netcdf = sorted(output_dir.glob("phase6_heuristic_severity_*.nc"))
    phase6_png = sorted(output_dir.glob("phase6_heuristic_severity_*.png"))

    assert len(phase2_markdown) == 1
    assert len(phase2_json) == 1
    assert len(phase2_netcdf) == 1
    assert len(phase2_png) == 1
    assert "Liquid cells: 2 / 6" in phase2_markdown[0].read_text(encoding="utf-8")
    assert len(phase5_markdown) == 1
    assert len(phase5_json) == 1
    assert len(phase5_netcdf) == 1
    assert len(phase5_png) == 1
    phase5_markdown_text = phase5_markdown[0].read_text(encoding="utf-8")
    assert "# Fase 5: riesgo aproximado de engelamiento" in phase5_markdown_text
    assert "Product kind: approximate proxy" in phase5_markdown_text
    assert "theta = T + 300 K" in phase5_markdown_text
    assert "Approximate icing risk in selected time: present" in phase5_markdown_text
    assert len(phase6_markdown) == 1
    assert len(phase6_json) == 1
    assert len(phase6_netcdf) == 1
    assert len(phase6_png) == 1
    phase6_markdown_text = phase6_markdown[0].read_text(encoding="utf-8")
    assert "# Fase 6: severidad heuristica y rangos relativos del modelo" in phase6_markdown_text
    assert "Severity class" in phase6_markdown_text
    assert "Relative bands" in phase6_markdown_text
    assert not any(output_dir.glob("phase4_heuristic_severity_*.md"))
    assert not any(output_dir.glob("phase4_heuristic_severity_*.json"))
    assert not any(output_dir.glob("phase4_heuristic_severity_*.nc"))
    assert not any(output_dir.glob("phase4_heuristic_severity_*.png"))
