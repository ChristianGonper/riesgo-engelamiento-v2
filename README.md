# Riesgo de Engelamiento

Proyecto Python + FastAPI + React para analizar un NetCDF WRF fijo, generar productos de riesgo de engelamiento y explorar el resultado en la interfaz interactiva `Aerofrost`.

## Estado actual
- El pipeline CLI valida el dataset y genera artefactos reproducibles de fases 1, 2, 5 y 6.
- El backend sirve `map-metadata`, `risk-map` y `cross-section` desde cache persistida en disco.
- El recálculo ya no ocurre al mover la línea temporal; solo se fuerza con `Recalcular archivo`.
- El frontend muestra estado de cache, overlay de mapa, cross-section expandible y reproducción temporal más estable.
- La cross-section distingue mejor el estado visual, mantiene `SFC / MAX` y añade referencias `Bajo / Medio / Alto`.

## Estructura principal
- `src/riesgo_engelamiento/`: pipeline científico, contratos y utilidades de cache.
- `src/backend/main.py`: API FastAPI para salud, metadata, mapa, cross-section y recálculo.
- `src/frontend/`: cliente React/Vite de `Aerofrost`.
- `tests/`: cobertura backend y del pipeline reproducible.
- `outputs/`: artefactos exportados por el CLI.
- `cache/derived/`: artefactos operativos reutilizados por la API.

## Quick Start
1. Instala dependencias Python: `uv sync --extra dev`
2. Ejecuta el pipeline base: `uv run riesgo-engelamiento --time-index 0`
3. Genera el entregable final: `uv run riesgo-engelamiento --time-index 0 --final-deliverable`
4. Ejecuta tests: `uv run --extra dev pytest`

## Aerofrost

### Backend
1. Instala dependencias del backend si aún no están: `uv pip install -r src/backend/requirements.txt`
2. Arranca la API: `uv run python src/backend/main.py`
3. La API queda en `http://127.0.0.1:8000`

### Frontend
1. Entra en `src/frontend`
2. Instala dependencias: `npm install`
3. Arranca desarrollo: `npm run dev`
4. Compila producción: `npm run build`

### Flujo en la UI
- `Perfil generico`: máximo vertical por columna.
- `Por flight level`: usa las franjas verticales derivadas en Python solo para el mapa horizontal.
- `Recalcular archivo`: rehace la cache del dataset activo.
- Línea temporal: cambia de tiempo sin relanzar cálculo científico pesado.
- Cross-section: selecciona dos puntos en el mapa para ver el perfil completo de superficie a máximo del modelo.
- Vista ampliada: permite inspección más cómoda del perfil vertical.

## Comandos útiles
| Comando | Descripción |
|---|---|
| `uv run riesgo-engelamiento --time-index 0` | Valida el dataset y genera productos de fases 1, 2, 5 y 6 |
| `uv run riesgo-engelamiento --time-index 0 --final-deliverable` | Exporta el entregable final canónico `presentation_final_deliverable_*` |
| `uv run riesgo-engelamiento --time-index 0 --final-product` | Usa el alias legado `presentation_final_product_*` |
| `uv run riesgo-engelamiento --time-index 0 --final-deliverable --final-product-band upper --final-product-highlighted-count 3` | Genera el entregable final y el comparativo compacto de tiempos destacados |
| `uv run --extra dev pytest` | Ejecuta toda la batería de pruebas |
| `npm run build` | Compila el frontend de `Aerofrost` |

## API actual
| Endpoint | Descripción |
|---|---|
| `GET /api/health` | Estado básico del servicio |
| `GET /api/map-metadata` | Metadata temporal, bounds y opciones verticales |
| `GET /api/cache-status` | Estado de cache del dataset activo |
| `POST /api/recalculate` | Recalcula la cache del dataset activo |
| `GET /api/risk-map` | Overlay de mapa por tiempo, modo y banda |
| `GET /api/cross-section` | Perfil vertical reutilizando base cacheada |

## Notas técnicas
- El dataset por defecto es `wrfout_d01_2015-04-17_18_00_00_corte`.
- La cache operativa vive en `cache/derived/` y se versiona con manifiesto.
- `generic / flight-level` afecta solo al mapa; no cambia la semántica del perfil vertical.
- La fase 5 sigue siendo una reconstrucción aproximada porque `PB` no está disponible.
- La fase 6 sigue siendo heurística; no se han cambiado las fórmulas meteorológicas.

## Documentación relacionada
- `plans/task_mejora_estructural_visualizacion.md`
- `plans/plan_riesgo_engelamiento.md`
- `specs/PRD_riesgo_engelamiento.md`
- `docs/decisions/`
