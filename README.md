# Riesgo de Engelamiento

Pipeline reproducible en Python para validar una salida WRF, documentar sus limitaciones y preparar las fases posteriores del análisis de engelamiento.

## Quick Start
1. Instalar dependencias para desarrollo y pruebas: `uv sync --extra dev`
2. Ejecutar la validación y las fases 2, 5 y 6 contra el dataset del repositorio: `uv run riesgo-engelamiento --time-index 0`
3. Ejecutar el entregable final canónico, que genera el mapa y resumen de presentación con nombre `presentation_final_deliverable_*`: `uv run riesgo-engelamiento --time-index 0 --final-deliverable`
4. Revisar los artefactos generados en `outputs/`

## UI Interactiva "Aero-Frost"
La nueva interfaz visual interactiva permite consultar el riesgo de engelamiento sobre un mapa y ver perfiles de corte transversal (cross-sections).
Para lanzarla:

**Backend (FastAPI):**
1. Instalar dependencias: `uv pip install -r src/backend/requirements.txt`
2. Arrancar el servidor: `uv run python src/backend/main.py`
   *(El servidor correrá en `http://127.0.0.1:8000`)*

**Frontend (React/Vite):**
1. Moverse a la carpeta del frontend: `cd src/frontend`
2. Instalar dependencias: `npm install --legacy-peer-deps`
3. Iniciar el modo de desarrollo: `npm run dev`
   *(La interfaz web estará disponible en la URL indicada por Vite, usualmente `http://localhost:5173`)*

Una vez abierta la interfaz web:
- **Mapa:** Puedes explorar visualmente las zonas (rojo = severo, amarillo = moderado, etc.).
- **Panel de control:** Usa los sliders de la parte inferior para seleccionar la altitud (FL) y la hora de pronóstico.
- **Cross-Section:** Haz clic en dos puntos diferentes del mapa para generar una línea de ruta. El panel inferior derecho mostrará automáticamente el corte transversal (perfil vertical) entre ambos puntos.
- **Threat Indicator:** El indicador NACA en la esquina superior derecha cambiará dinámicamente mostrando la amenaza aerodinámica máxima detectada.

## Commands
| Command | Description |
|---|---|
| `uv run riesgo-engelamiento --time-index 0` | Valida el dataset, genera el resumen de fase 1 y exporta los productos de fases 2, 5 y 6 |
| `uv run riesgo-engelamiento --time-index 0 --final-deliverable` | Ejecuta el flujo anterior y ademas exporta el entregable final canónico, con nombre `presentation_final_deliverable_*`, para el tiempo seleccionado |
| `uv run riesgo-engelamiento --time-index 0 --final-product` | Alias legado del entregable final; conserva el prefijo histórico `presentation_final_product_*` por compatibilidad |
| `uv run riesgo-engelamiento --time-index 0 --final-deliverable --final-product-band upper --final-product-highlighted-count 3` | Genera el entregable canónico y, si se pide, el comparativo compacto de tiempos destacados como artefacto compañero |
| `uv run --extra dev pytest` | Ejecuta la batería de pruebas |

## Architecture
- `src/riesgo_engelamiento/dataset.py`: apertura y validación del NetCDF.
- `src/riesgo_engelamiento/summary.py`: construcción del resumen legible y JSON.
- `src/riesgo_engelamiento/phase2.py`: derivación de la máscara binaria líquida, salida NetCDF y mapa PNG.
- `src/riesgo_engelamiento/phase5.py`: reconstrucción aproximada de theta, presión y riesgo de engelamiento.
- `src/riesgo_engelamiento/phase3.py`: alias de compatibilidad para la Phase 5.
- `src/riesgo_engelamiento/phase6.py`: severidad heurística canónica y rangos relativos de niveles.
- `src/riesgo_engelamiento/final_product.py`: contrato, resumen y mapa del entregable final canónico, con compatibilidad para el alias legado.
- `src/riesgo_engelamiento/phase4.py`: alias de compatibilidad para la severidad heurística.
- `src/riesgo_engelamiento/cli.py`: entrada principal reproducible con `--final-deliverable` como ruta canónica.

## Project Docs
- PRD: `specs/PRD_riesgo_engelamiento.md`
- Plan: `plans/plan_riesgo_engelamiento.md`
- Session handoff: `docs/session_2026-04-12_handoff.md`
- ADRs: `docs/decisions/`
- ADR canónico del entregable final: `docs/decisions/ADR-006-canonical-final-deliverable-mode.md`

## Notes
- La constante base de temperatura potencial usada en esta primera fase es `T0 = 300 K`.
- La salida de fase 1 es deliberadamente descriptiva: valida entradas, expone supuestos y deja marcadas las limitaciones del archivo.
- La fase 2 produce una máscara binaria horizontal a partir de `QCLOUD + QRAIN` para un tiempo seleccionado.
- La fase 5 reconstruye `theta = T + 300`, aproxima la presión desde `ZNW` y `P`, y etiqueta el riesgo como proxy documentado porque `PB` no está disponible.
- La fase 6 clasifica la severidad de forma heurística a partir del riesgo aproximado, la fracción líquida, la coexistencia con hielo, la persistencia temporal y la ocupación relativa por bandas de `eta`.
- El entregable final canónico usa el prefijo `presentation_final_deliverable_*`; el alias legado `--final-product` sigue generando `presentation_final_product_*` para compatibilidad.
- Los artefactos técnicos siguen siendo `phase2_*`, `phase5_*` y `phase6_*`.
- El comparativo de tiempos destacados sigue siendo un artefacto compañero, no el entregable canónico principal.

