from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

REPO_SRC = Path(__file__).resolve().parents[1]
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from riesgo_engelamiento.config import DEFAULT_DATASET_NAME
from riesgo_engelamiento.cache_store import IcingCacheStore
from riesgo_engelamiento.dataset import open_dataset
from riesgo_engelamiento.web_api import (
    build_cross_section_payload,
    build_map_metadata,
    build_risk_map_payload,
)

app = FastAPI(title="Aero-Frost Icing Risk API")

DATASET_PATH = Path(__file__).resolve().parents[2] / DEFAULT_DATASET_NAME
CACHE_STORE = IcingCacheStore(DATASET_PATH)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "aerofrost-api",
        "datasetPath": str(DATASET_PATH),
    }


def _load_dataset():
    return open_dataset(DATASET_PATH)


@app.get("/api/map-metadata")
async def map_metadata():
    with _load_dataset() as dataset:
        return CACHE_STORE.map_metadata(dataset, build_map_metadata)


@app.get("/api/cache-status")
async def cache_status():
    with _load_dataset() as dataset:
        return CACHE_STORE.build_status(dataset).to_dict()


@app.post("/api/recalculate")
async def recalculate_cache():
    try:
        with _load_dataset() as dataset:
            metadata = CACHE_STORE.prime(dataset, build_map_metadata)
            return {
                "status": "recalculated",
                "metadata": metadata,
                "cacheStatus": CACHE_STORE.build_status(dataset).to_dict(),
            }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/risk-map")
async def risk_map(
    time_index: int = Query(0, alias="timeIndex"),
    mode: str = Query("generic"),
    vertical_option: str | None = Query(None, alias="verticalOption"),
):
    try:
        with _load_dataset() as dataset:
            cache_key = f"t{time_index}_m{mode}_v{vertical_option or 'none'}"
            return CACHE_STORE.get_or_build(
                "risk-map",
                cache_key,
                lambda: build_risk_map_payload(
                    dataset,
                    DATASET_PATH,
                    time_index=time_index,
                    mode=mode,
                    vertical_option=vertical_option,
                ),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/cross-section")
async def cross_section(
    time_index: int = Query(0, alias="timeIndex"),
    route_start_lat: float = Query(..., alias="routeStartLat"),
    route_start_lon: float = Query(..., alias="routeStartLon"),
    route_end_lat: float = Query(..., alias="routeEndLat"),
    route_end_lon: float = Query(..., alias="routeEndLon"),
    route_points: int = Query(160, alias="routePoints"),
):
    try:
        with _load_dataset() as dataset:
            cache_key = (
                f"t{time_index}_"
                f"{route_start_lat:.4f}_{route_start_lon:.4f}_"
                f"{route_end_lat:.4f}_{route_end_lon:.4f}_p{route_points}"
            )
            return CACHE_STORE.get_or_build(
                "cross-section",
                cache_key,
                lambda: build_cross_section_payload(
                    dataset,
                    DATASET_PATH,
                    time_index=time_index,
                    route_start_lat=route_start_lat,
                    route_start_lon=route_start_lon,
                    route_end_lat=route_end_lat,
                    route_end_lon=route_end_lon,
                    route_points=route_points,
                ),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )
