from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from riesgo_engelamiento.config import (
    APPROXIMATE_POISSON_KAPPA,
    APPROXIMATE_PRESSURE_SURFACE_PA,
    APPROXIMATE_PRESSURE_TOP_PA,
    ASSUMPTIONS,
    CORE_T0_K,
)
from riesgo_engelamiento.phase5 import build_phase5_approximate_risk_product, write_phase5_outputs


def _build_phase5_dataset(include_znw: bool = True) -> xr.Dataset:
    time = np.array(["2015-04-17T18:00:00"], dtype="datetime64[ns]")
    bottom_top = 2
    south_north = 2
    west_east = 2
    bottom_top_stag = bottom_top + 1

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    theta_perturbation = np.zeros_like(qcloud)
    pressure_perturbation = np.zeros_like(qcloud)
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)
    vertical = np.array([[1.0, 0.5, 0.0]], dtype=np.float32)

    qcloud[0, 0, 0, 0] = 1.0
    qrain[0, 1, 1, 1] = 1.0

    data_vars: dict[str, tuple[tuple[str, ...], np.ndarray]] = {
        "QCLOUD": (("Time", "bottom_top", "south_north", "west_east"), qcloud),
        "QRAIN": (("Time", "bottom_top", "south_north", "west_east"), qrain),
        "T": (("Time", "bottom_top", "south_north", "west_east"), theta_perturbation),
        "P": (("Time", "bottom_top", "south_north", "west_east"), pressure_perturbation),
        "XLAT": (("Time", "south_north", "west_east"), horizontal + 40.0),
        "XLONG": (("Time", "south_north", "west_east"), horizontal - 3.0),
    }
    if include_znw:
        data_vars["ZNW"] = (("Time", "bottom_top_stag"), vertical)

    return xr.Dataset(
        data_vars=data_vars,
        coords={"XTIME": (("Time",), time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def test_phase5_reconstructs_theta_pressure_temperature_and_risk_masks() -> None:
    dataset = _build_phase5_dataset()
    product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)

    expected_pressure_upper = APPROXIMATE_PRESSURE_TOP_PA + 0.75 * (
        APPROXIMATE_PRESSURE_SURFACE_PA - APPROXIMATE_PRESSURE_TOP_PA
    )
    expected_pressure_lower = APPROXIMATE_PRESSURE_TOP_PA + 0.25 * (
        APPROXIMATE_PRESSURE_SURFACE_PA - APPROXIMATE_PRESSURE_TOP_PA
    )
    expected_temperature_upper = CORE_T0_K * (expected_pressure_upper / 100000.0) ** APPROXIMATE_POISSON_KAPPA
    expected_temperature_lower = CORE_T0_K * (expected_pressure_lower / 100000.0) ** APPROXIMATE_POISSON_KAPPA

    assert np.allclose(product.theta.values, CORE_T0_K)
    assert np.isclose(product.pressure_proxy.values[0, 0, 0], expected_pressure_upper)
    assert np.isclose(product.pressure_proxy.values[1, 0, 0], expected_pressure_lower)
    assert np.isclose(product.temperature_proxy.values[0, 0, 0], expected_temperature_upper, atol=1e-5)
    assert np.isclose(product.temperature_proxy.values[1, 0, 0], expected_temperature_lower, atol=1e-5)
    assert product.liquid_horizontal_cell_count == 2
    assert product.liquid_vertical_cell_count == 2
    assert product.risk_horizontal_cell_count == 1
    assert product.risk_vertical_cell_count == 1
    assert product.has_liquid is True
    assert product.has_risk is True
    assert np.count_nonzero(product.risk_presence.values) == 1
    assert product.to_dict()["phase"] == 5
    assert product.to_dict()["product_kind"] == "approximate proxy"
    assert "Approximation notes" in product.to_markdown()


def test_phase5_writes_artifacts_and_exports_proxy_fields(tmp_path: Path) -> None:
    dataset = _build_phase5_dataset()
    product = build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    markdown_path, json_path, netcdf_path, png_path = write_phase5_outputs(product, tmp_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert netcdf_path.exists()
    assert png_path.exists()

    written = xr.open_dataset(netcdf_path)
    assert set(
        ["theta", "pressure_proxy", "temperature_proxy", "temperature_c_proxy", "liquid_presence_3d", "risk_presence_3d", "liquid_amount", "liquid_presence", "risk_presence"]
    ).issubset(written.data_vars)
    assert written.attrs["title"].startswith("Phase 5 approximate icing-risk diagnostic")
    assert written.attrs["product_kind"] == "approximate proxy"
    assert float(written["risk_presence"].sum()) == 1.0


def test_phase5_requires_znw_for_eta_proxy() -> None:
    dataset = _build_phase5_dataset(include_znw=False)

    with pytest.raises(ValueError, match="ZNW"):
        build_phase5_approximate_risk_product(dataset, "synthetic.nc", time_index=0)


def test_phase5_pressure_assumption_matches_config_constants() -> None:
    assumption = ASSUMPTIONS[1]

    assert f"{APPROXIMATE_PRESSURE_SURFACE_PA / 100:.0f} hPa" in assumption
    assert f"{APPROXIMATE_PRESSURE_TOP_PA / 100:.0f} hPa" in assumption
