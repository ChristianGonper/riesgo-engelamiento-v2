from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr

from riesgo_engelamiento import cli
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE
from riesgo_engelamiento.route_profile import (
    build_route_icing_profile_figure,
    build_route_icing_profile_product,
    write_route_icing_profile_outputs,
)


def _build_route_profile_dataset() -> xr.Dataset:
    time = np.array(
        ["2015-04-17T18:00:00", "2015-04-17T21:00:00"], dtype="datetime64[ns]"
    )
    bottom_top = 3
    south_north = 3
    west_east = 3

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    qice = np.zeros_like(qcloud)
    theta = np.zeros_like(qcloud)
    pressure = np.zeros_like(qcloud)
    vertical = np.array(
        [[1.0, 0.66, 0.33, 0.0], [1.0, 0.66, 0.33, 0.0]], dtype=np.float32
    )
    lat0 = np.array(
        [
            [40.0, 40.0, 40.0],
            [40.5, 40.5, 40.5],
            [41.0, 41.0, 41.0],
        ],
        dtype=np.float32,
    )
    lon0 = np.array(
        [
            [-3.0, -2.5, -2.0],
            [-3.0, -2.5, -2.0],
            [-3.0, -2.5, -2.0],
        ],
        dtype=np.float32,
    )
    xlat = np.stack([lat0, lat0], axis=0)
    xlon = np.stack([lon0, lon0], axis=0)

    qcloud[0, 2, :, :] = 1.0
    qrain[0, 2, :, :] = 1.0
    qice[0, 2, :, :] = 1.0
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
            "XLAT": (EXPECTED_DIMS_BY_VARIABLE["XLAT"], xlat),
            "XLONG": (EXPECTED_DIMS_BY_VARIABLE["XLONG"], xlon),
        },
        coords={"XTIME": (EXPECTED_DIMS_BY_VARIABLE["XTIME"], time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def test_route_profile_builds_distance_and_profile_shape() -> None:
    dataset = _build_route_profile_dataset()
    product = build_route_icing_profile_product(
        dataset,
        "synthetic.nc",
        time_index=0,
        route_start_lat=40.0,
        route_start_lon=-3.0,
        route_end_lat=41.0,
        route_end_lon=-2.0,
        route_points=6,
    )

    assert product.profile.shape == (3, 6)
    assert np.all(np.diff(product.distance_km) >= 0.0)
    assert product.distance_km[0] == 0.0
    assert product.distance_km[-1] > 0.0
    assert np.nanmin(product.profile) >= 0.0
    assert np.nanmax(product.profile) <= 100.0
    assert "risk_presence" in product.severity_formula
    payload = product.to_dict()
    assert payload["artifact_kind"] == "presentation/route-icing-profile"
    assert payload["route_point_count"] == 6
    assert payload["profile_shape"] == [3, 6]
    assert payload["visualBands"][0]["label"] == "Bajo"


def test_route_profile_render_creates_expected_axes() -> None:
    dataset = _build_route_profile_dataset()
    product = build_route_icing_profile_product(
        dataset,
        "synthetic.nc",
        time_index=0,
        route_start_lat=40.0,
        route_start_lon=-3.0,
        route_end_lat=41.0,
        route_end_lon=-2.0,
        route_points=10,
    )
    figure = build_route_icing_profile_figure(product)
    try:
        assert len(figure.axes) == 2
        profile_axis, colorbar_axis = figure.axes
        assert profile_axis.get_xlabel() == "Distancia acumulada (km)"
        assert profile_axis.get_ylabel() == "eta_mid (nivel relativo)"
        assert colorbar_axis.get_ylabel() == "Severidad heuristica (0-100)"
        assert (
            profile_axis.get_title(loc="left")
            == "Perfil de severidad de engelamiento en ruta"
        )
    finally:
        plt.close(figure)


def test_route_profile_writes_outputs(tmp_path: Path) -> None:
    dataset = _build_route_profile_dataset()
    product = build_route_icing_profile_product(
        dataset,
        "synthetic.nc",
        time_index=0,
        route_start_lat=40.0,
        route_start_lon=-3.0,
        route_end_lat=41.0,
        route_end_lon=-2.0,
        route_points=8,
    )
    markdown_path, json_path, png_path = write_route_icing_profile_outputs(
        product, tmp_path
    )

    assert markdown_path.exists()
    assert json_path.exists()
    assert png_path.exists()
    assert markdown_path.name.startswith("route_icing_profile_t000")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["artifact_kind"] == "presentation/route-icing-profile"
    assert payload["route_point_count"] == 8
    assert payload["outputs"]["png"].endswith(".png")


def test_route_profile_rejects_points_outside_domain() -> None:
    dataset = _build_route_profile_dataset()
    with pytest.raises(ValueError, match="outside the dataset geographic domain"):
        build_route_icing_profile_product(
            dataset,
            "synthetic.nc",
            time_index=0,
            route_start_lat=39.0,
            route_start_lon=-3.0,
            route_end_lat=41.0,
            route_end_lon=-2.0,
            route_points=6,
        )


def test_main_writes_route_profile_when_requested(tmp_path: Path, monkeypatch) -> None:
    dataset = _build_route_profile_dataset()
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
            "--route-profile",
            "--route-start-lat",
            "40.0",
            "--route-start-lon",
            "-3.0",
            "--route-end-lat",
            "41.0",
            "--route-end-lon",
            "-2.0",
            "--route-points",
            "10",
        ]
    )

    assert exit_code == 0
    route_markdown = sorted(output_dir.glob("route_icing_profile_*.md"))
    route_json = sorted(output_dir.glob("route_icing_profile_*.json"))
    route_png = sorted(output_dir.glob("route_icing_profile_*.png"))
    assert len(route_markdown) == 1
    assert len(route_json) == 1
    assert len(route_png) == 1


def test_main_route_profile_requires_coordinates(tmp_path: Path, monkeypatch) -> None:
    dataset = _build_route_profile_dataset()
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
            "--route-profile",
            "--route-start-lat",
            "40.0",
        ]
    )

    assert exit_code == 1
