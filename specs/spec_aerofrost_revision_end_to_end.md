# Spec: Revision end-to-end de AeroFrost para mapa, perfiles y cross-section

## Objective

Actualizar la aplicacion web AeroFrost para que deje de ser un mock visual y pase a reflejar el comportamiento operativo ya disponible en el pipeline Python.

Objetivos funcionales:
- Renombrar la aplicacion visible en frontend como `Aerofrost`.
- Sustituir el overlay mock del mapa por datos reales calculados previamente en backend.
- Ofrecer dos modos de visualizacion del riesgo en mapa:
  - `Perfil generico`: mostrar, para cada punto del mapa, la severidad maxima presente en cualquier flight level / nivel vertical disponible.
  - `Por flight level`: permitir seleccionar un FL y mostrar la severidad siguiendo exactamente la logica disponible en Python; si Python trabaja por franjas, la web mostrara esas mismas franjas.
- Corregir la reproduccion temporal del frontend para que el modo Play/Pause avance automaticamente.
- Sustituir el cross-section mock por un corte vertical real de la ruta seleccionada, usando el calculo backend ya existente o una extension directa de este, mostrando desde el suelo hasta el nivel maximo disponible.
- Permitir ampliar el cross-section para verlo mas grande sin perder la ruta activa.

Usuarios objetivo:
- Analista meteorologico que necesita ver rapidamente donde hay riesgo y en que severidad.
- Usuario de briefing operacional que necesita comparar mapa horizontal y corte vertical sobre una ruta.

## Tech Stack

- Backend: Python 3.11+, FastAPI, Uvicorn, xarray, netCDF4, numpy.
- Pipeline cientifico existente: `src/riesgo_engelamiento`.
- Frontend: React 19, TypeScript, Vite, Leaflet, Recharts/Layer SVG custom segun convenga.
- Testing backend: Pytest.
- Testing frontend: por introducir, preferiblemente Vitest + React Testing Library si no existe ya.

## Commands

- Instalar dependencias Python: `uv sync --extra dev`
- Arrancar backend API: `uv run python src/backend/main.py`
- Ejecutar pipeline reproducible base: `uv run riesgo-engelamiento --time-index 0`
- Generar entregable final actual: `uv run riesgo-engelamiento --time-index 0 --final-deliverable`
- Generar perfil de ruta actual por CLI: `uv run riesgo-engelamiento --time-index 0 --route-profile --route-start-lat 40.0 --route-start-lon -3.0 --route-end-lat 41.0 --route-end-lon -2.0 --route-points 200`
- Instalar frontend: `npm install --legacy-peer-deps` (en `src/frontend`)
- Desarrollo frontend: `npm run dev` (en `src/frontend`)
- Build frontend: `npm run build` (en `src/frontend`)
- Lint frontend: `npm run lint` (en `src/frontend`)
- Tests backend: `uv run --extra dev pytest`

## Project Structure

- `src/riesgo_engelamiento/` -> pipeline cientifico y productos derivados reutilizables.
- `src/riesgo_engelamiento/route_profile.py` -> calculo actual del perfil vertical en ruta y render estatico.
- `src/riesgo_engelamiento/final_product.py` -> proyecciones 2D y artefactos finales existentes.
- `src/backend/main.py` -> API FastAPI a ampliar para servir mapa, tiempos, niveles y cross-section.
- `src/frontend/src/` -> aplicacion React/Vite que hoy contiene una UI mostly mock en `App.tsx`.
- `tests/` -> pruebas Python del pipeline y de integracion backend que se anadiran aqui si siguen la convencion actual.
- `specs/` -> especificaciones vivas del producto y de esta revision.
- `plans/` -> plan tecnico y task breakdown posteriores a la aprobacion de esta spec.

## Code Style

Convenciones esperadas:
- Python: funciones pequenas, validacion temprana, dataclasses para contratos publicos, nombres explicitos en `snake_case`.
- TypeScript/React: componentes pequenos, estado derivado minimizado, tipos explicitos para payloads API, nombres en `PascalCase` para componentes y `camelCase` para funciones.
- Evitar mocks incrustados en el render final; los datos deben entrar por clientes API o adapters dedicados.

Ejemplo de estilo objetivo:

```ts
type RiskMode = 'generic' | 'flight-level'

function buildMapRequest(mode: RiskMode, timeIndex: number, flightLevel: number | null) {
  return {
    mode,
    timeIndex,
    flightLevel,
  }
}
```

## Testing Strategy

- Backend:
  - mantener Pytest como framework principal;
  - cubrir contrato de nuevos endpoints (`/api/health`, `/api/map-metadata`, `/api/risk-map`, `/api/cross-section` o equivalentes);
  - validar errores claros ante tiempos, FLs o rutas fuera de dominio;
  - verificar que el modo generico y el modo por FL devuelven matrices/overlays coherentes con los productos precalculados.
- Frontend:
  - introducir pruebas de componentes y estado para selector de modo, slider FL y autoplay temporal;
  - verificar que el cambio de tiempo o modo dispara la peticion esperada y actualiza mapa/cross-section;
  - verificar que el cross-section solo usa la ruta seleccionada y no puntos mock.
- Verificacion manual:
  - mapa con nombre `Aerofrost` en cabecera;
  - autoplay funcional;
  - modo generico mostrando riesgo maximo regional cuando exista;
  - modo FL mostrando diferencias al cambiar niveles o franjas conforme a Python;
  - cross-section mostrando distancia horizontal, nivel vertical desde suelo hasta maximo y severidad en color;
  - cross-section ampliable desde la interfaz.

## Boundaries

- Always:
  - reutilizar el calculo cientifico ya existente antes de reimplementar formulas;
  - mantener trazabilidad entre frontend, API y productos del pipeline;
  - ejecutar pruebas relevantes antes de dar por cerrada la implementacion;
  - etiquetar claramente cualquier salida como proxy heuristico cuando corresponda.
- Ask first:
  - cambios de contrato que rompan JSON existentes en `outputs/` o artefactos CLI ya usados;
  - nuevas dependencias grandes de frontend o backend;
  - cambios de semantica cientifica en severidad, bandas o niveles.
- Never:
  - dejar overlays mock como si fueran datos reales;
  - duplicar logica cientifica del pipeline en React;
  - eliminar caveats cientificos del producto proxy;
  - comprometer secretos o datos no reproducibles.

## Success Criteria

- La cabecera del frontend muestra `Aerofrost` y no `frontend` ni textos de plantilla.
- El frontend deja de renderizar poligonos y cross-sections mock hardcodeados.
- Existe un modo `Perfil generico` que, para cada celda/pixel/punto del mapa, representa la severidad maxima disponible en toda la columna vertical.
- Existe un modo `Por flight level` con selector de FL, y el mapa cambia realmente al variar el nivel o franja definida por Python.
- El modo `Por flight level` sigue la misma semantica de niveles o franjas disponible en la implementacion Python; la web no inventa otra discretizacion.
- El control temporal Play/Pause avanza automaticamente por los tiempos disponibles y refresca el mapa sin interaccion manual adicional.
- El backend expone metadata suficiente para poblar tiempos y niveles disponibles en frontend.
- El backend expone un endpoint de mapa que sirve datos precalculados o derivados del pipeline, sin calculo cientifico en el cliente.
- El backend expone un endpoint de cross-section que devuelve el perfil de la ruta seleccionada.
- El cross-section del frontend representa:
  - eje horizontal = posicion a lo largo de la ruta seleccionada;
  - eje vertical = perfil vertical completo desde suelo hasta nivel maximo disponible;
  - color = severidad.
- Cambiar el tiempo refresca tanto el mapa como el cross-section para la misma ruta activa.
- El usuario puede ampliar el cross-section a una vista mayor y volver a contraerlo.
- La revision end-to-end queda cubierta por pruebas backend y, cuando se introduzcan, pruebas frontend minimas de estado/controles.

## Open Questions

- Confirmar el formato de overlay para el mapa en la API: raster JSON liviano, GeoJSON derivado o imagen georreferenciada servida por backend.
- Decidir si el backend debe leer directamente el dataset WRF en cada peticion o cachear en memoria productos precalculados por tiempo/modo.

## Current Findings

- `src/frontend/src/App.tsx` usa overlays y cross-section completamente mock, y el boton Play/Pause no tiene temporizador real.
- `src/backend/main.py` solo expone `/api/health`; aun no hay endpoints de mapa ni de cross-section.
- El pipeline Python ya dispone de calculo reutilizable para perfil de ruta en `src/riesgo_engelamiento/route_profile.py`.
- El producto final actual ya proyecta severidad horizontal, pero la API todavia no lo expone al frontend.
