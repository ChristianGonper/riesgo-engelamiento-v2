# Spec: Refinamiento visual de Aerofrost

## Objective
Reducir el aspecto de demo tecnica en la interfaz de `Aerofrost` y dejar una presentacion mas limpia, operativa y orientada a uso real.

Usuario principal:
- Pilotos, despachadores y usuarios operativos que consultan riesgo de engelamiento en una interfaz visual.

Problema actual:
- La UI muestra varios textos tecnicos o de estado interno (`backend Python`, `overlay real`, `artefactos cacheados`, `modo, tiempo y ruta`) que hacen la aplicacion menos limpia.
- Cuando no hay engelamiento, el mapa conserva un color de fondo visible en el overlay, en vez de verse transparente.
- La tarjeta superior derecha usa una presentacion demasiado tecnica (`Perfil generico`, `Modo por flight level`, `10 / 100`) en vez de una lectura mas simple.
- El control `Recalcular archivo` ocupa demasiado peso visual en la columna izquierda.

Objetivo de producto:
- Mantener el flujo actual de mapa, timeline, perfil y recarga de cache, pero con un lenguaje visual y textual mas propio de una aplicacion real.

## Tech Stack
- Frontend: React 19 + TypeScript + Vite 7 + Tailwind CSS 4 + React Leaflet
- Backend: Python 3.11 + FastAPI
- Contratos UI/API afectados: `src/frontend/src/App.tsx`, `src/frontend/src/api.ts`, y si hace falta la generacion del overlay en backend para soportar transparencia real

## Commands
- Instalar dependencias Python: `uv sync --extra dev`
- Ejecutar tests backend: `uv run --extra dev pytest`
- Arrancar API: `uv run python src/backend/main.py`
- Instalar frontend: `npm install`
- Desarrollo frontend: `npm run dev`
- Build frontend: `npm run build`

## Project Structure
- `src/frontend/src/App.tsx` -> layout principal, textos operativos, tarjetas y controles
- `src/frontend/src/index.css` -> tokens visuales globales y utilidades base
- `src/frontend/src/api.ts` -> contratos tipados con la API
- `src/backend/main.py` -> endpoints FastAPI consumidos por la UI
- `src/riesgo_engelamiento/` -> logica cientifica y generacion de productos/cache
- `tests/` -> pruebas backend y pipeline
- `specs/` -> especificaciones vivas del proyecto

## Code Style
Seguir el estilo ya presente: componentes funcionales, estado local con hooks, helpers pequenos y copy de UI corto y directo.

```tsx
const threatValue = riskMap?.severityRange[1] ?? 0
const threatLabel = severityLabel(threatValue)
const threatColor = severityColor(threatValue)

<span
  className="rounded-full border px-3 py-1 text-[10px] font-bold tracking-[0.24em]"
  style={{ borderColor: threatColor, color: threatColor }}
>
  {threatLabel}
</span>
```

Convenciones:
- mantener TypeScript estricto y nombres explicitos;
- reutilizar helpers existentes antes de introducir nuevos componentes;
- priorizar copy en espanol limpio para estado operativo;
- evitar etiquetas tecnicas visibles al usuario salvo que aporten accion clara.

## Testing Strategy
- Nivel principal: verificacion manual de UI en desarrollo local con backend levantado
- Build gate frontend: `npm run build`
- Regression gate backend: `uv run --extra dev pytest`
- Si se toca generacion de overlay o payloads, validar que:
  - el endpoint `GET /api/risk-map` sigue respondiendo;
  - la transparencia no rompe bounds ni carga del mapa;
  - la UI sigue renderizando mapa, timeline y cross-section sin errores de tipos.

## Boundaries
- Always:
  - conservar el flujo funcional actual de mapa, timeline, seleccion de ruta y cross-section;
  - mantener `Recalcular archivo` disponible, aunque cambie de posicion o peso visual;
  - ejecutar `npm run build` antes de cerrar la implementacion;
  - ejecutar `uv run --extra dev pytest` si hay cambios de backend.
- Ask first:
  - cambiar contratos de API o nombres de campos ya consumidos por frontend;
  - introducir dependencias nuevas;
  - alterar el comportamiento cientifico del calculo de severidad, no solo su presentacion.
- Never:
  - eliminar la accion de recarga de cache;
  - romper la sincronizacion tiempo/mapa/perfil;
  - exponer secretos o tocar datos del dataset fuera del alcance visual.

## Success Criteria
- Las zonas del overlay sin engelamiento se renderizan transparentes, de forma que se vea limpio el mapa base.
- La tarjeta superior derecha deja de mostrar copy tipo `Perfil generico`, `Modo por flight level` y `x / 100`, y pasa a una presentacion mas simple basada en `PERFIL` y `Aerodynamic threat`.
- La columna izquierda conserva `Aerofrost`, pero elimina referencias a:
  - `Mapa operativo conectado al backend Python...`
  - `artefactos cacheados`
  - mensajes de estilo demo tecnica equivalentes.
- El mensaje inicial deja de decir `Selecciona modo, tiempo y ruta.` y usa un copy mas limpio y neutral.
- El texto `Mapa alimentado por overlay real del backend.` desaparece del panel inferior.
- El boton `Recalcular archivo` deja de ocupar una posicion principal en la columna izquierda y se convierte en un control pequeno y discreto en otra zona coherente de la UI.
- La interfaz final sigue siendo plenamente funcional en desktop y no degrada la experiencia movil existente.

## Open Questions
- Ninguna bloqueante. Se usara el copy aprobado por defecto:
  - titulo: `Aerofrost`
  - subtitulo: `Plataforma operativa de riesgo de engelamiento`
  - tarjeta derecha: `PERFIL`
  - etiqueta: `Aerodynamic threat`
