# Riesgo de Engelamiento

Pipeline reproducible en Python para validar una salida WRF, documentar sus limitaciones y preparar las fases posteriores del análisis de engelamiento.

## Quick Start
1. Instalar dependencias para desarrollo y pruebas: `uv sync --extra dev`
2. Ejecutar la validación y la fase 2 contra el dataset del repositorio: `uv run riesgo-engelamiento --time-index 0`
3. Revisar los artefactos generados en `outputs/`

## Commands
| Command | Description |
|---|---|
| `uv run riesgo-engelamiento --time-index 0` | Valida el dataset, genera el resumen de fase 1 y exporta la máscara binaria de fase 2 |
| `uv run --extra dev pytest` | Ejecuta la batería de pruebas |

## Architecture
- `src/riesgo_engelamiento/dataset.py`: apertura y validación del NetCDF.
- `src/riesgo_engelamiento/summary.py`: construcción del resumen legible y JSON.
- `src/riesgo_engelamiento/phase2.py`: derivación de la máscara binaria líquida, salida NetCDF y mapa PNG.
- `src/riesgo_engelamiento/cli.py`: entrada principal reproducible.

## Notes
- La constante base de temperatura potencial usada en esta primera fase es `T0 = 300 K`.
- La salida de fase 1 es deliberadamente descriptiva: valida entradas, expone supuestos y deja marcadas las limitaciones del archivo.
- La fase 2 produce una máscara binaria horizontal a partir de `QCLOUD + QRAIN` para un tiempo seleccionado.

