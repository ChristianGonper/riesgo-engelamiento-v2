from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from .phase5 import build_phase5_approximate_risk_product
from .phase6 import build_phase6_heuristic_severity_product


def build_severity_volume(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    *,
    time_index: int,
) -> tuple[xr.DataArray, str, dict[str, Any]]:
    phase5 = build_phase5_approximate_risk_product(
        dataset, dataset_path, time_index=time_index
    )
    phase6 = build_phase6_heuristic_severity_product(
        dataset, dataset_path, time_index=time_index
    )
    selected = dataset.isel(Time=time_index)
    liquid_3d = (selected["QCLOUD"].fillna(0) + selected["QRAIN"].fillna(0) > 0).astype(
        np.float32
    )
    ice_3d = (selected["QICE"].fillna(0) > 0).astype(np.float32)
    mixed_3d = (liquid_3d > 0) & (ice_3d > 0)
    risk_3d = phase5.risk_presence_3d.astype(np.float32)
    coherence_3d = 1.0 - np.abs(risk_3d - liquid_3d)
    severity_3d = (
        0.50 * risk_3d
        + 0.25 * liquid_3d
        + 0.15 * mixed_3d.astype(np.float32)
        + 0.10 * coherence_3d
    ) * 100.0
    severity_3d = xr.where(risk_3d > 0, severity_3d, 0.0)
    severity_3d = severity_3d.clip(0.0, 100.0).astype(np.float32)
    formula = "100 * (0.50*risk_presence + 0.25*liquid_presence + 0.15*mixed_phase + 0.10*coherence)"
    source_metrics = {
        "phase6_severity_class": phase6.severity_class,
        "phase6_severity_score": float(phase6.severity_score),
        "phase6_dominant_band": phase6.dominant_band,
        "phase6_persistence_fraction": float(phase6.persistence_fraction),
    }
    return severity_3d, formula, source_metrics


__all__ = ["build_severity_volume"]
