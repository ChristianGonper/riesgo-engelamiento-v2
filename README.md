# Riesgo de Engelamiento

Pipeline reproducible en Python para validar una salida WRF, documentar sus limitaciones y preparar las fases posteriores del análisis de engelamiento.

## Quick Start
1. Instalar dependencias: `uv sync`
2. Ejecutar la fase 1 contra el dataset del repositorio: `uv run riesgo-engelamiento`
3. Revisar los artefactos generados en `outputs/`

## Commands
| Command | Description |
|---|---|
| `uv run riesgo-engelamiento` | Valida el dataset y genera el resumen de fase 1 |
| `uv run pytest` | Ejecuta la batería de pruebas |

## Architecture
- `src/riesgo_engelamiento/dataset.py`: apertura y validación del NetCDF.
- `src/riesgo_engelamiento/summary.py`: construcción del resumen legible y JSON.
- `src/riesgo_engelamiento/cli.py`: entrada principal reproducible.

## Notes
- La constante base de temperatura potencial usada en esta primera fase es `T0 = 300 K`.
- La salida de fase 1 es deliberadamente descriptiva: valida entradas, expone supuestos y deja marcadas las limitaciones del archivo.

