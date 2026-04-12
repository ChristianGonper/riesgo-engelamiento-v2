from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.phase4 import build_phase4_heuristic_severity_product, write_phase4_outputs


def _build_phase4_dataset() -> xr.Dataset:
    time = np.array(["2015-04-17T18:00:00", "2015-04-17T21:00:00"], dtype="datetime64[ns]")
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


def test_phase4_builds_band_summary_and_temporal_severity() -> None:
    dataset = _build_phase4_dataset()
    product = build_phase4_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)

    assert product.severity_class == "moderate"
    assert product.severity_class_time == ("moderate", "severe")
    assert product.dominant_band == "lower"
    assert len(product.band_summaries) == 3
    assert product.band_summaries[2].selected_risk_fraction > product.band_summaries[0].selected_risk_fraction
    assert "bottom_top 2-2" in product.selected_active_level_ranges[0]
    assert np.isclose(product.time_risk_horizontal_fraction.values[0], 0.25)
    assert np.isclose(product.time_risk_horizontal_fraction.values[1], 1.0)
    assert np.isclose(product.time_persistence_fraction.values[0], 1.0)
    assert np.isclose(product.time_persistence_fraction.values[1], 1.0)
    assert np.isclose(product.time_active_level_fraction.values[0], 1 / 3)
    assert np.isclose(product.time_active_level_fraction.values[1], 2 / 3)
    assert "Relative bands" in product.to_markdown()
    assert "Temporal severity" in product.to_markdown()


def test_phase4_writes_artifacts_and_exports_summary_fields(tmp_path: Path) -> None:
    dataset = _build_phase4_dataset()
    product = build_phase4_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)
    markdown_path, json_path, netcdf_path, png_path = write_phase4_outputs(product, tmp_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert netcdf_path.exists()
    assert png_path.exists()

    written = xr.open_dataset(netcdf_path)
    assert set(
        [
            "selected_liquid_level_fraction",
            "selected_ice_level_fraction",
            "selected_mixed_level_fraction",
            "selected_risk_level_fraction",
            "time_persistence_fraction",
            "time_severity_score",
            "time_severity_class_index",
            "band_selected_risk_fraction",
        ]
    ).issubset(written.data_vars)
    assert written.attrs["dominant_band"] == "lower"
    assert "eta_mid" in written.coords


def test_phase4_requires_qice() -> None:
    dataset = _build_phase4_dataset().drop_vars("QICE")

    with pytest.raises(ValueError, match="QICE"):
        build_phase4_heuristic_severity_product(dataset, "synthetic.nc", time_index=0)


def test_phase4_score_for_previous_time_is_not_changed_by_future_extension() -> None:
    prefix = _build_phase4_dataset()
    extended = prefix.copy(deep=True)

    qcloud = extended["QCLOUD"].values.copy()
    qrain = extended["QRAIN"].values.copy()
    qice = extended["QICE"].values.copy()
    qcloud = np.concatenate([qcloud, np.ones_like(qcloud[:1]) * 2.0, np.ones_like(qcloud[:1]) * 2.0], axis=0)
    qrain = np.concatenate([qrain, np.ones_like(qrain[:1]) * 2.0, np.ones_like(qrain[:1]) * 2.0], axis=0)
    qice = np.concatenate([qice, np.ones_like(qice[:1]) * 2.0, np.ones_like(qice[:1]) * 2.0], axis=0)
    t = np.concatenate([extended["T"].values, np.zeros_like(extended["T"].values[:1]), np.zeros_like(extended["T"].values[:1])], axis=0)
    p = np.concatenate([extended["P"].values, np.zeros_like(extended["P"].values[:1]), np.zeros_like(extended["P"].values[:1])], axis=0)
    xlat = np.concatenate([extended["XLAT"].values, extended["XLAT"].values[:1], extended["XLAT"].values[:1]], axis=0)
    xlong = np.concatenate([extended["XLONG"].values, extended["XLONG"].values[:1], extended["XLONG"].values[:1]], axis=0)
    xtime = np.array(
        [
            "2015-04-17T18:00:00",
            "2015-04-17T21:00:00",
            "2015-04-18T00:00:00",
            "2015-04-18T03:00:00",
        ],
        dtype="datetime64[ns]",
    )

    extended = xr.Dataset(
        data_vars={
            "QCLOUD": (EXPECTED_DIMS_BY_VARIABLE["QCLOUD"], qcloud),
            "QRAIN": (EXPECTED_DIMS_BY_VARIABLE["QRAIN"], qrain),
            "QICE": (EXPECTED_DIMS_BY_VARIABLE["QICE"], qice),
            "T": (EXPECTED_DIMS_BY_VARIABLE["T"], t),
            "P": (EXPECTED_DIMS_BY_VARIABLE["P"], p),
            "ZNW": (("Time", "bottom_top_stag"), np.concatenate([extended["ZNW"].values, extended["ZNW"].values[:1], extended["ZNW"].values[:1]], axis=0)),
            "XLAT": (EXPECTED_DIMS_BY_VARIABLE["XLAT"], xlat),
            "XLONG": (EXPECTED_DIMS_BY_VARIABLE["XLONG"], xlong),
        },
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], xtime)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )

    prefix_product = build_phase4_heuristic_severity_product(prefix, "synthetic.nc", time_index=1)
    extended_product = build_phase4_heuristic_severity_product(extended, "synthetic.nc", time_index=1)

    assert np.isclose(prefix_product.severity_score_time.values[1], extended_product.severity_score_time.values[1])
    assert prefix_product.severity_class_time[1] == extended_product.severity_class_time[1]
