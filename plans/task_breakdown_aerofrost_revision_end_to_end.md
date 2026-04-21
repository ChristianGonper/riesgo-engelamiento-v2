# Task Breakdown: Revision end-to-end de Aerofrost

## Overview

Este desglose convierte `plans/plan_aerofrost_revision_end_to_end.md` en tareas pequenas, verificables y ordenadas por dependencia. El objetivo es reducir primero el riesgo backend, estabilizar contratos y despues conectar la UI real sin volver a introducir mocks.

## Phase 1: Backend Risk Reduction and Contracts

- [ ] Task: Confirmar semantica Python de niveles y franjas
  - Acceptance: queda identificado si la seleccion vertical para web usa niveles discretos, franjas o ambas; la decision queda reflejada en el adapter backend
  - Verify: inspeccion manual del codigo Python relevante y prueba local del adapter con un ejemplo real
  - Files: `src/riesgo_engelamiento/`, `plans/plan_aerofrost_revision_end_to_end.md`

- [ ] Task: Elegir formato inicial del payload de `risk-map`
  - Acceptance: queda decidido un formato de respuesta inicial que el frontend pueda consumir y que sea compatible con autoplay
  - Verify: generar un ejemplo de payload y revisar su tamano/estructura manualmente
  - Files: `src/backend/main.py`, `src/riesgo_engelamiento/`

- [ ] Task: Implementar endpoint `/api/map-metadata`
  - Acceptance: el endpoint devuelve tiempos disponibles, modos soportados y opciones verticales reales derivadas de Python
  - Verify: `uv run --extra dev pytest` con test del endpoint y comprobacion manual del JSON
  - Files: `src/backend/main.py`, `tests/`

- [ ] Task: Implementar endpoint `/api/risk-map` para modo `generic`
  - Acceptance: el endpoint acepta `timeIndex` y devuelve severidad maxima vertical por columna sin usar datos mock
  - Verify: `uv run --extra dev pytest` con test de contrato y comprobacion manual comparando respuestas entre tiempos
  - Files: `src/backend/main.py`, `src/riesgo_engelamiento/`, `tests/`

- [ ] Task: Implementar endpoint `/api/risk-map` para modo `flight-level`
  - Acceptance: el endpoint acepta seleccion vertical y devuelve severidad coherente con la logica Python de nivel o franja
  - Verify: `uv run --extra dev pytest` con test de contrato y caso invalido por FL/franja no soportada
  - Files: `src/backend/main.py`, `src/riesgo_engelamiento/`, `tests/`

- [ ] Task: Implementar endpoint `/api/cross-section`
  - Acceptance: el endpoint recibe ruta y `timeIndex`, y devuelve distancia, eje vertical completo y matriz de severidad desde suelo hasta maximo
  - Verify: `uv run --extra dev pytest` con test valido y test fuera de dominio
  - Files: `src/backend/main.py`, `src/riesgo_engelamiento/route_profile.py`, `tests/`

## Checkpoint: Backend Contracts Stable

- [ ] Tests backend relevantes pasan
- [ ] La semantica vertical ya no es ambigua
- [ ] El formato del payload del mapa es aceptable para primera iteracion
- [ ] `metadata`, `risk-map` y `cross-section` estan listos para consumo frontend

## Phase 2: Frontend Data Wiring

- [ ] Task: Extraer tipos y cliente API del frontend
  - Acceptance: existen tipos TypeScript para metadata, mapa y cross-section; `App.tsx` deja de contener fetches improvisados
  - Verify: `npm run build` en `src/frontend`
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Introducir estado global minimo de aplicacion
  - Acceptance: el frontend gestiona `timeIndex`, `riskMode`, `selectedFlightLevelBand`, `route`, `isPlaying` y `isCrossSectionExpanded`
  - Verify: `npm run build` y comprobacion manual de que la app inicia sin errores
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Renombrar la UI visible a `Aerofrost`
  - Acceptance: la cabecera visible usa `Aerofrost` y desaparecen restos de texto de plantilla o nombres genericos
  - Verify: comprobacion manual en navegador
  - Files: `src/frontend/src/App.tsx`

- [ ] Task: Reemplazar overlays mock del mapa por datos reales
  - Acceptance: desaparecen los poligonos hardcodeados y el mapa se alimenta del endpoint `/api/risk-map`
  - Verify: `npm run build` y comprobacion manual cambiando tiempo para ver respuesta real
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Implementar selector de modo `generic` / `flight-level`
  - Acceptance: el usuario puede cambiar de modo y la UI muestra u oculta la seleccion vertical segun metadata
  - Verify: `npm run build` y comprobacion manual de cambio de modo
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Implementar selector de FL o franjas reales
  - Acceptance: la UI presenta las opciones verticales reales del backend y no inventa discretizaciones locales
  - Verify: `npm run build` y comprobacion manual de que el cambio altera el mapa
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Activar autoplay real de la linea temporal
  - Acceptance: Play avanza automaticamente por los tiempos disponibles y Pause lo detiene sin perder sincronizacion
  - Verify: `npm run build` y comprobacion manual del avance automatico
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

## Checkpoint: Frontend Connected to Real Data

- [ ] `npm run build` pasa
- [ ] La app ya no usa overlays mock
- [ ] Nombre `Aerofrost` visible
- [ ] Modo y selector vertical funcionan con datos reales
- [ ] Autoplay actualiza el mapa correctamente

## Phase 3: Cross-Section Real and Expanded View

- [ ] Task: Sustituir el cross-section mock por render real
  - Acceptance: al seleccionar una ruta, el panel muestra una visualizacion real del endpoint `/api/cross-section`
  - Verify: `npm run build` y comprobacion manual seleccionando dos puntos
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Sincronizar cross-section con `timeIndex`
  - Acceptance: si hay ruta activa, cambiar el tiempo refresca el corte vertical real sin perder la ruta
  - Verify: `npm run build` y comprobacion manual con Play/Pause y cambio manual de tiempo
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Mostrar el perfil vertical completo desde suelo hasta maximo
  - Acceptance: el render del cross-section usa el eje vertical completo devuelto por backend y no recorta al FL activo
  - Verify: comprobacion manual del panel y, si aplica, test de transformacion/render
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/`

- [ ] Task: Anadir control de ampliar/contraer cross-section
  - Acceptance: el usuario puede ampliar el panel a una vista mayor y volver a la vista normal sin perder estado
  - Verify: `npm run build` y comprobacion manual de ampliar/contraer
  - Files: `src/frontend/src/App.tsx`, `src/frontend/src/index.css`, `src/frontend/src/`

## Checkpoint: Main User Flow Works End-to-End

- [ ] Seleccion de ruta funcional
- [ ] Cross-section real visible
- [ ] Tiempo sincroniza mapa y cross-section
- [ ] Vista ampliada disponible

## Phase 4: Validation and Closeout

- [ ] Task: Endurecer tests backend para errores y contratos
  - Acceptance: quedan cubiertos parametros invalidos, rutas fuera de dominio y respuestas minimas de los endpoints nuevos
  - Verify: `uv run --extra dev pytest`
  - Files: `tests/`, `src/backend/main.py`

- [ ] Task: Anadir pruebas frontend minimas para controles criticos
  - Acceptance: existe cobertura minima para selector de modo, autoplay o sincronizacion basica de estado
  - Verify: comando de tests frontend si se introduce; si no existe aun, dejarlo preparado y documentado
  - Files: `src/frontend/src/`, configuracion de tests frontend si aplica

- [ ] Task: Actualizar documentacion operativa minima
  - Acceptance: `README.md` explica como levantar backend y frontend con el flujo real actualizado
  - Verify: lectura manual y arranque siguiendo la documentacion
  - Files: `README.md`

- [ ] Task: Validacion final contra la spec aprobada
  - Acceptance: se comprueba que los criterios de `specs/spec_aerofrost_revision_end_to_end.md` se cumplen
  - Verify: `uv run --extra dev pytest`, `npm run build`, y checklist manual end-to-end
  - Files: `specs/spec_aerofrost_revision_end_to_end.md`, `README.md`, `tests/`, `src/backend/main.py`, `src/frontend/src/App.tsx`

## Final Checkpoint

- [ ] Backend estable y sin mocks
- [ ] Frontend conectado a endpoints reales
- [ ] `generic` y `flight-level` reflejan la logica Python
- [ ] Autoplay real funcionando
- [ ] Cross-section real, completa y ampliable
- [ ] Build y pruebas relevantes pasan

## Recommended Execution Order

1. Tareas backend de Phase 1 completas antes de tocar el flujo principal del frontend.
2. Tareas de wiring de Phase 2 antes de trabajar en la UX del cross-section.
3. Tareas de Phase 3 antes del cierre de validacion.
4. Phase 4 solo cuando el flujo principal ya funcione manualmente.

## Notes on Scope

- Si alguna tarea empieza a tocar mas de 5 archivos con logica heterogenea, debe dividirse.
- Si el payload de mapa resulta demasiado pesado durante Phase 1, hay que volver al plan y ajustar el contrato antes de seguir con autoplay.
- Si `route_profile.py` no encaja limpio como API interactiva, conviene extraer un adapter backend dedicado en vez de acoplar la UI al renderer PNG.
