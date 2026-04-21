from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

import xarray as xr

from .config import (
    CACHE_DERIVED_DIR_NAME,
    CACHE_MANIFEST_NAME,
    CACHE_METADATA_NAME,
    CACHE_ROOT_DIR_NAME,
    CACHE_STATUS_NAME,
    CACHE_VERSION,
)

T = TypeVar("T")


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, xr.DataArray):
        return value.to_dict()
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


@dataclass(frozen=True, slots=True)
class CacheStatus:
    dataset_path: str
    dataset_id: str
    cache_dir: str
    cache_version: str
    state: str
    last_recalculated_at: str | None
    metadata_cached: bool
    artifact_count: int
    available_times: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "datasetPath": self.dataset_path,
            "datasetId": self.dataset_id,
            "cacheDir": self.cache_dir,
            "cacheVersion": self.cache_version,
            "state": self.state,
            "lastRecalculatedAt": self.last_recalculated_at,
            "metadataCached": self.metadata_cached,
            "artifactCount": self.artifact_count,
            "availableTimes": self.available_times,
        }


class IcingCacheStore:
    def __init__(
        self, dataset_path: str | Path, cache_root: str | Path | None = None
    ) -> None:
        self.dataset_path = Path(dataset_path)
        self.cache_root = (
            Path(cache_root)
            if cache_root is not None
            else self.dataset_path.parent / CACHE_ROOT_DIR_NAME
        )
        self.cache_dir = self.cache_root / CACHE_DERIVED_DIR_NAME

    def _dataset_fingerprint(self) -> str:
        stat = self.dataset_path.stat()
        payload = f"{self.dataset_path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{CACHE_VERSION}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _dataset_cache_dir(self) -> Path:
        return self.cache_dir / self._dataset_fingerprint()

    def _manifest_path(self) -> Path:
        return self._dataset_cache_dir() / CACHE_MANIFEST_NAME

    def _metadata_path(self) -> Path:
        return self._dataset_cache_dir() / CACHE_METADATA_NAME

    def _status_path(self) -> Path:
        return self._dataset_cache_dir() / CACHE_STATUS_NAME

    def _artifact_paths(self) -> list[Path]:
        if not self._dataset_cache_dir().exists():
            return []
        return [
            path for path in self._dataset_cache_dir().glob("*.json") if path.is_file()
        ]

    def _read_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default),
            encoding="utf-8",
        )

    def _load_manifest(self) -> dict[str, Any] | None:
        manifest_path = self._manifest_path()
        if not manifest_path.exists():
            return None
        try:
            return self._read_json(manifest_path)
        except json.JSONDecodeError:
            return None

    def _ensure_dataset_dir(self) -> Path:
        dataset_dir = self._dataset_cache_dir()
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir

    def clear(self) -> None:
        if self._dataset_cache_dir().exists():
            shutil.rmtree(self._dataset_cache_dir())

    def _write_manifest(self, dataset: xr.Dataset) -> dict[str, Any]:
        manifest = {
            "datasetPath": str(self.dataset_path),
            "datasetId": self._dataset_fingerprint(),
            "cacheVersion": CACHE_VERSION,
            "generatedAt": _utc_now(),
            "timeCount": int(dataset.sizes.get("Time", 0)),
            "times": [
                {"index": int(index), "label": label}
                for index, label in self._available_times(dataset)
            ],
        }
        self._write_json(self._manifest_path(), manifest)
        self._write_json(self._status_path(), {**manifest, "state": "ready"})
        return manifest

    def _available_times(self, dataset: xr.Dataset) -> list[tuple[int, str]]:
        from .web_api import _selected_time_label

        time_count = int(dataset.sizes.get("Time", 0))
        return [
            (index, _selected_time_label(dataset, index) or f"t{index:03d}")
            for index in range(time_count)
        ]

    def prime(
        self,
        dataset: xr.Dataset,
        metadata_builder: Callable[[xr.Dataset, str | Path], dict[str, Any]],
    ) -> dict[str, Any]:
        self.clear()
        self._ensure_dataset_dir()
        manifest = self._write_manifest(dataset)
        metadata = metadata_builder(dataset, self.dataset_path)
        self._write_json(self._metadata_path(), metadata)
        self._write_json(
            self._status_path(), {**manifest, "state": "ready", "metadataCached": True}
        )
        return metadata

    def build_status(self, dataset: xr.Dataset) -> CacheStatus:
        manifest = self._load_manifest()
        if manifest is None:
            manifest = self._write_manifest(dataset)
            metadata_cached = False
        else:
            metadata_cached = self._metadata_path().exists()
        return CacheStatus(
            dataset_path=str(self.dataset_path),
            dataset_id=manifest["datasetId"],
            cache_dir=str(self._dataset_cache_dir()),
            cache_version=CACHE_VERSION,
            state="ready" if metadata_cached else "warming",
            last_recalculated_at=manifest.get("generatedAt"),
            metadata_cached=metadata_cached,
            artifact_count=len(self._artifact_paths()),
            available_times=list(manifest.get("times", [])),
        )

    def get_or_build(self, name: str, key: str, builder: Callable[[], T]) -> T:
        safe_name = f"{name}-{key}.json"
        path = self._dataset_cache_dir() / safe_name
        if path.exists():
            return self._read_json(path)
        result = builder()
        self._write_json(path, result)
        return result

    def map_metadata(
        self,
        dataset: xr.Dataset,
        builder: Callable[[xr.Dataset, str | Path], dict[str, Any]],
    ) -> dict[str, Any]:
        metadata_path = self._metadata_path()
        if metadata_path.exists():
            return self._read_json(metadata_path)
        metadata = builder(dataset, self.dataset_path)
        self._ensure_dataset_dir()
        self._write_json(metadata_path, metadata)
        return metadata
