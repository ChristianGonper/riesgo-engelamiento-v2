from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_DATASET_NAME, DEFAULT_OUTPUT_DIR_NAME
from .dataset import DatasetValidationError, assert_valid, open_dataset, validate_dataset
from .summary import build_phase1_summary, write_phase1_outputs


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_dataset_path() -> Path:
    return _repo_root() / DEFAULT_DATASET_NAME


def _default_output_dir() -> Path:
    return _repo_root() / DEFAULT_OUTPUT_DIR_NAME


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fase 1 del proyecto de riesgo de engelamiento.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_default_dataset_path(),
        help="Ruta al archivo WRF a validar.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Directorio donde se escriben los resúmenes de fase 1.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        return 1

    with open_dataset(args.dataset) as dataset:
        validation = validate_dataset(dataset, source=args.dataset)
        summary = build_phase1_summary(dataset, validation, args.dataset)
        markdown_path, json_path = write_phase1_outputs(summary, args.output_dir)

        if not validation.is_valid:
            print(validation.to_markdown(), file=sys.stderr)
            try:
                assert_valid(validation)
            except DatasetValidationError as exc:
                print(str(exc), file=sys.stderr)
                print(f"Validation artifacts written to: {markdown_path}", file=sys.stderr)
                print(f"Validation artifacts written to: {json_path}", file=sys.stderr)
                return 1

    print()
    print(summary.to_markdown())
    print()
    print(f"Markdown summary written to: {markdown_path}")
    print(f"JSON summary written to: {json_path}")
    return 0
