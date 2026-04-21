from __future__ import annotations

import importlib.util
import asyncio
from pathlib import Path

import numpy as np
import xarray as xr
from fastapi import HTTPException

from riesgo_engelamiento.cache_store import IcingCacheStore
from riesgo_engelamiento.config import EXPECTED_DIMS_BY_VARIABLE


def _load_backend_main_module():
    module_path = Path(__file__).resolve().parents[1] / "src" / "backend" / "main.py"
    spec = importlib.util.spec_from_file_location("backend_main", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_backend_dataset() -> xr.Dataset:
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

    qcloud[0, 2, 0, 0] = 1.0
    qrain[0, 2, 0, 0] = 1.0
    qice[0, 2, 0, 0] = 1.0
    qcloud[0, 0, 2, 2] = 1.0
    qrain[0, 0, 2, 2] = 1.0
    qice[0, 0, 2, 2] = 1.0
    qcloud[1, 1, :, :] = 1.0
    qrain[1, 1, :, :] = 1.0
    qice[1, 1, :, :] = 1.0

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


class _DatasetContext:
    def __init__(self, dataset: xr.Dataset) -> None:
        self._dataset = dataset

    def __enter__(self) -> xr.Dataset:
        return self._dataset

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _patch_dataset_and_cache(
    monkeypatch, backend_main, dataset: xr.Dataset, cache_root: Path
) -> None:
    monkeypatch.setattr(backend_main, "_load_dataset", lambda: _DatasetContext(dataset))
    monkeypatch.setattr(
        backend_main,
        "CACHE_STORE",
        IcingCacheStore(backend_main.DATASET_PATH, cache_root),
    )


def test_map_metadata_reports_python_vertical_options(
    monkeypatch, tmp_path: Path
) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    payload = asyncio.run(backend_main.map_metadata())
    assert payload["timeCount"] == 2
    assert payload["riskModes"][0]["id"] == "generic"
    assert payload["verticalSelection"]["kind"] == "python-band"
    assert {item["id"] for item in payload["verticalSelection"]["options"]} == {
        "dominant",
        "upper",
        "middle",
        "lower",
    }


def test_cache_status_and_recalculate_endpoint(monkeypatch, tmp_path: Path) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    cache_status = asyncio.run(backend_main.cache_status())
    recalculated = asyncio.run(backend_main.recalculate_cache())

    assert cache_status["datasetPath"].endswith("wrfout_d01_2015-04-17_18_00_00_corte")
    assert recalculated["status"] == "recalculated"
    assert recalculated["cacheStatus"]["metadataCached"] is True


def test_risk_map_supports_generic_and_band_modes(monkeypatch, tmp_path: Path) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    generic_payload = asyncio.run(
        backend_main.risk_map(time_index=0, mode="generic", vertical_option=None)
    )
    lower_payload = asyncio.run(
        backend_main.risk_map(
            time_index=0, mode="flight-level", vertical_option="lower"
        )
    )

    assert generic_payload["overlayImage"].startswith("data:image/png;base64,")
    assert lower_payload["resolvedVerticalOption"] == "lower"
    assert generic_payload["severityRange"][1] >= lower_payload["severityRange"][1]


def test_risk_map_rejects_invalid_vertical_option(monkeypatch, tmp_path: Path) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    try:
        asyncio.run(
            backend_main.risk_map(
                time_index=0, mode="flight-level", vertical_option="bad-band"
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Unsupported vertical option" in str(exc.detail)
    else:
        raise AssertionError("Expected HTTPException for invalid vertical option")


def test_cross_section_returns_surface_to_maximum_profile(
    monkeypatch, tmp_path: Path
) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    payload = asyncio.run(
        backend_main.cross_section(
            time_index=0,
            route_start_lat=40.0,
            route_start_lon=-3.0,
            route_end_lat=41.0,
            route_end_lon=-2.0,
            route_points=6,
        )
    )

    assert payload["profile_shape"] == [3, 6]
    assert payload["verticalExtent"] == "surface-to-maximum"
    assert payload["xAxisLabel"] == "Distancia acumulada (km)"
    assert payload["visualBands"][1]["label"] == "Medio"


def test_cross_section_rejects_route_outside_domain(
    monkeypatch, tmp_path: Path
) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, tmp_path / "cache")

    try:
        asyncio.run(
            backend_main.cross_section(
                time_index=0,
                route_start_lat=39.0,
                route_start_lon=-3.0,
                route_end_lat=41.0,
                route_end_lon=-2.0,
                route_points=6,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "outside the dataset geographic domain" in str(exc.detail)
    else:
        raise AssertionError("Expected HTTPException for route outside domain")


def test_risk_map_reuses_cached_artifact(monkeypatch, tmp_path: Path) -> None:
    backend_main = _load_backend_main_module()
    dataset = _build_backend_dataset()
    cache_root = tmp_path / "cache"
    _patch_dataset_and_cache(monkeypatch, backend_main, dataset, cache_root)

    first_payload = asyncio.run(
        backend_main.risk_map(time_index=1, mode="generic", vertical_option=None)
    )
    second_payload = asyncio.run(
        backend_main.risk_map(time_index=1, mode="generic", vertical_option=None)
    )

    cache_status = asyncio.run(backend_main.cache_status())
    assert first_payload["overlayImage"] == second_payload["overlayImage"]
    assert cache_status["artifactCount"] >= 1
    assert any(cache_root.glob("derived/**/*.json"))
