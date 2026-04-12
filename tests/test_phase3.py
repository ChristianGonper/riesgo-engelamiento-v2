from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr

from riesgo_engelamiento.phase3 import build_phase3_approximate_risk_product, write_phase3_outputs


def _build_phase3_dataset() -> xr.Dataset:
    time = np.array(["2015-04-17T18:00:00"], dtype="datetime64[ns]")
    bottom_top = 2
    south_north = 2
    west_east = 2
    bottom_top_stag = bottom_top + 1

    qcloud = np.zeros((time.size, bottom_top, south_north, west_east), dtype=np.float32)
    qrain = np.zeros_like(qcloud)
    theta = np.zeros_like(qcloud)
    pressure = np.zeros_like(qcloud)
    horizontal = np.zeros((time.size, south_north, west_east), dtype=np.float32)
    vertical = np.array([[1.0, 0.5, 0.0]], dtype=np.float32)

    qcloud[0, 0, 0, 0] = 1.0

    return xr.Dataset(
        data_vars={
            "QCLOUD": (("Time", "bottom_top", "south_north", "west_east"), qcloud),
            "QRAIN": (("Time", "bottom_top", "south_north", "west_east"), qrain),
            "T": (("Time", "bottom_top", "south_north", "west_east"), theta),
            "P": (("Time", "bottom_top", "south_north", "west_east"), pressure),
            "ZNW": (("Time", "bottom_top_stag"), vertical),
            "XLAT": (("Time", "south_north", "west_east"), horizontal + 40.0),
            "XLONG": (("Time", "south_north", "west_east"), horizontal - 3.0),
        },
        coords={"XTIME": (("Time",), time)},
        attrs={"TITLE": "synthetic wrfout", "START_DATE": "2015-04-17_18:00:00"},
    )


def test_phase3_writes_legacy_phase3_filenames_and_labels(tmp_path: Path) -> None:
    dataset = _build_phase3_dataset()
    product = build_phase3_approximate_risk_product(dataset, "synthetic.nc", time_index=0)
    markdown_path, json_path, netcdf_path, png_path = write_phase3_outputs(product, tmp_path)

    assert markdown_path.name.startswith("phase3_approximate_icing_risk_")
    assert json_path.name.startswith("phase3_approximate_icing_risk_")
    assert netcdf_path.name.startswith("phase3_approximate_icing_risk_")
    assert png_path.name.startswith("phase3_approximate_icing_risk_")
    assert "# Fase 3: riesgo aproximado de engelamiento" in markdown_path.read_text(encoding="utf-8")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["phase"] == 3
    assert payload["product_kind"] == "approximate proxy"

    written = xr.open_dataset(netcdf_path)
    assert written.attrs["phase"] == 3
    assert written.attrs["title"].startswith("Phase 3 approximate icing-risk diagnostic")
