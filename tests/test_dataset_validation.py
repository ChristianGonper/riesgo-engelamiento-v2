from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

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
    assert "T0 = 300 K" in summary.to_markdown()


def test_validate_dataset_reports_missing_inputs_and_raises_on_request() -> None:
    dataset = _build_dataset(include_qrain=False, include_bottom_top_stag=False)
    report = validate_dataset(dataset, source="synthetic.nc")

    assert not report.is_valid
    assert "QRAIN" in report.error_message()
    assert "bottom_top_stag" in report.error_message()

    with pytest.raises(DatasetValidationError):
        assert_valid(report)

