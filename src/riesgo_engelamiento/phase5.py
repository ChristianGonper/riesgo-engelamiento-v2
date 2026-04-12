from __future__ import annotations

from pathlib import Path

from .phase3 import (
    Phase5ApproximateRiskProduct,
    _write_approximate_risk_outputs,
    build_phase3_approximate_risk_product,
)


def build_phase5_approximate_risk_product(
    dataset,
    dataset_path: str | Path,
    time_index: int = 0,
) -> Phase5ApproximateRiskProduct:
    return build_phase3_approximate_risk_product(dataset, dataset_path, time_index=time_index)


def write_phase5_outputs(
    product: Phase5ApproximateRiskProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    return _write_approximate_risk_outputs(product, output_dir, phase_number=5)


__all__ = [
    "Phase5ApproximateRiskProduct",
    "build_phase5_approximate_risk_product",
    "write_phase5_outputs",
]
