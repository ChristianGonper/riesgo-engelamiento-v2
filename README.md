# Riesgo de Engelamiento

Pipeline reproducible en Python para validar una salida WRF, documentar sus limitaciones y preparar las fases posteriores del análisis de engelamiento.

## Quick Start
1. Instalar dependencias para desarrollo y pruebas: `uv sync --extra dev`
2. Ejecutar la validación y las fases 2, 5 y 6 contra el dataset del repositorio: `uv run riesgo-engelamiento --time-index 0`
3. Revisar los artefactos generados en `outputs/`

## Commands
| Command | Description |
|---|---|
| `uv run riesgo-engelamiento --time-index 0` | Valida el dataset, genera el resumen de fase 1 y exporta los productos de fases 2, 5 y 6 |
| `uv run --extra dev pytest` | Ejecuta la batería de pruebas |

## Architecture
- `src/riesgo_engelamiento/dataset.py`: apertura y validación del NetCDF.
- `src/riesgo_engelamiento/summary.py`: construcción del resumen legible y JSON.
- `src/riesgo_engelamiento/phase2.py`: derivación de la máscara binaria líquida, salida NetCDF y mapa PNG.
- `src/riesgo_engelamiento/phase5.py`: reconstrucción aproximada de theta, presión y riesgo de engelamiento.
- `src/riesgo_engelamiento/phase3.py`: alias de compatibilidad para la Phase 5.
- `src/riesgo_engelamiento/phase6.py`: severidad heurística canónica y rangos relativos de niveles.
- `src/riesgo_engelamiento/phase4.py`: alias de compatibilidad para la severidad heurística.
- `src/riesgo_engelamiento/cli.py`: entrada principal reproducible.

## Project Docs
- PRD: `specs/PRD_riesgo_engelamiento.md`
- Plan: `plans/plan_riesgo_engelamiento.md`
- Session handoff: `docs/session_2026-04-12_handoff.md`
- ADRs: `docs/decisions/`

## Notes
- La constante base de temperatura potencial usada en esta primera fase es `T0 = 300 K`.
- La salida de fase 1 es deliberadamente descriptiva: valida entradas, expone supuestos y deja marcadas las limitaciones del archivo.
- La fase 2 produce una máscara binaria horizontal a partir de `QCLOUD + QRAIN` para un tiempo seleccionado.
- La fase 5 reconstruye `theta = T + 300`, aproxima la presión desde `ZNW` y `P`, y etiqueta el riesgo como proxy documentado porque `PB` no está disponible.
- La fase 6 clasifica la severidad de forma heurística a partir del riesgo aproximado, la fracción líquida, la coexistencia con hielo, la persistencia temporal y la ocupación relativa por bandas de `eta`.

