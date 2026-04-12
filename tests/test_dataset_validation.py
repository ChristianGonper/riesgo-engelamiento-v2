from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from riesgo_engelamiento import cli
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.dataset import DatasetValidationError, assert_valid, validate_dataset
from riesgo_engelamiento.summary import build_phase1_summary


def _build_dataset(include_qrain: bool = True, include_bottom_top_stag: bool = True) -> xr.Dataset:
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

    return xr.Dataset(
        data_vars=data_vars,
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

