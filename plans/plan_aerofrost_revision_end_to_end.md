# Implementation Plan: Revision end-to-end de Aerofrost

## Overview

Vamos a convertir la UI actual de `src/frontend` desde una maqueta visual a una aplicacion conectada al pipeline Python existente. El trabajo se centra en exponer en FastAPI productos reutilizables del backend cientifico, consumirlos desde React, reflejar fielmente la semantica Python para niveles o franjas, activar la reproduccion temporal real y reemplazar el cross-section mock por un perfil vertical operativo ampliable.

## Architecture Decisions

- **Backend como adaptador del pipeline existente**: FastAPI no recalcula la ciencia desde cero; envuelve `src/riesgo_engelamiento` y expone contratos JSON consumibles por la web.
- **Backend-first para reducir riesgo**: se prioriza resolver primero semantica vertical, contratos y rendimiento de payload en backend antes del refactor fuerte del frontend.
- **Semantica vertical dictada por Python**: el modo `Por flight level` se alimenta de la misma logica de niveles o franjas que use el codigo Python, para evitar divergencia entre CLI y web.
- **Mapa en dos modos claros**: `generic` usa maximo vertical por columna; `flight-level` usa el nivel o franja seleccionada segun Python.
- **Cross-section completo e independiente del selector FL**: el corte muestra siempre desde suelo hasta el nivel maximo disponible, sincronizado con tiempo y ruta.
- **Frontend orientado a estado remoto**: React debe centralizar `timeIndex`, `riskMode`, `selectedFlightLevelBand`, `route`, `autoplay` y `expandedCrossSection`, y disparar fetches derivados a la API.
- **Contratos pequenos y trazables**: antes de refactor visual profundo, se define un contrato estable para metadata, overlay del mapa y cross-section.

## Dependency Graph

```text
Python pipeline outputs / semantics
    |
    +-- Backend adapters for metadata and vertical semantics
    |       |
    |       +-- /api/map-metadata
    |       +-- /api/risk-map
    |       +-- /api/cross-section
    |               |
    |               +-- Frontend typed API client
    |                       |
    |                       +-- App state model
    |                       +-- Map rendering
    |                       +-- Timeline autoplay
    |                       +-- Cross-section panel / expanded view
    |
    +-- Backend tests for contracts
            |
            +-- Frontend tests for controls and synchronization
```

## Implementation Order

1. Hacer primero trabajo de backend para cerrar riesgos: contratos, semantica vertical, serializacion y volumen de datos.
2. Implementar adapters backend sobre el pipeline Python existente.
3. Verificar backend con tests de contrato y pruebas manuales de payload antes de tocar la UI.
4. Sustituir mocks frontend por cliente API y estado real cuando los endpoints ya sean estables.
5. Activar autoplay y sincronizacion de mapa/cross-section.
6. Anadir ampliacion del cross-section y rematar validacion end-to-end.

## Phases

### Phase 1: Backend Risk Reduction, Contracts and Scientific Adapters

Objetivo: dejar un backend capaz de describir tiempos, niveles o franjas, overlays de mapa y cross-sections reales, reduciendo antes los riesgos de semantica y rendimiento.

#### Task 0: Spike backend de semantica vertical y tamano de payload

**Description:** Hacer una exploracion tecnica pequena en backend para fijar como se representa exactamente la seleccion por FL/franja y medir que formato de respuesta de mapa es viable para autoplay y consumo React.

**Acceptance criteria:**
- [ ] Queda documentado si Python expone niveles discretos, franjas o ambas cosas para la UI.
- [ ] Queda elegida una estrategia inicial de payload para `risk-map`.
- [ ] Se identifican limites razonables para cache o serializacion si hicieran falta.

**Verification:**
- [ ] Revision manual del adapter y de ejemplos de payload.
- [ ] Se actualiza este plan si la exploracion cambia alguna decision tecnica.

**Dependencies:** None

**Files likely touched:**
- `plans/plan_aerofrost_revision_end_to_end.md`
- `src/riesgo_engelamiento/` modulo adaptador o script de exploracion corto
- posible nota en `docs/` si hace falta

**Estimated scope:** Small

#### Task 1: Definir contrato de metadata para tiempos y verticalidad

**Description:** Crear una capa backend que describa tiempos disponibles, nombre visible del dataset, modos soportados y opciones verticales derivadas de Python para el selector de FL/franjas.

**Acceptance criteria:**
- [ ] Existe un endpoint de metadata que devuelve tiempos disponibles y opciones verticales utilizables por la UI.
- [ ] La metadata distingue claramente modo `generic` y modo `flight-level`.
- [ ] La respuesta documenta si las opciones verticales son niveles discretos o franjas.

**Verification:**
- [ ] Tests backend pasan para el endpoint de metadata.
- [ ] Manual check: `uv run python src/backend/main.py` y consulta al endpoint devuelve JSON coherente.

**Dependencies:** Task 0

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/` modulo adaptador nuevo o existente
- `tests/` nuevo test backend de metadata

**Estimated scope:** Medium

#### Task 2: Exponer overlay real del mapa en modo generico y por FL/franja

**Description:** Implementar el endpoint de mapa para tiempo seleccionado y modo de riesgo, reutilizando la proyeccion horizontal existente y anadiendo la seleccion por nivel o franja conforme a Python.

**Acceptance criteria:**
- [ ] El endpoint acepta `timeIndex` y `mode`.
- [ ] El modo `generic` devuelve severidad maxima vertical por columna.
- [ ] El modo `flight-level` devuelve severidad consistente con la logica Python de nivel o franja seleccionada.

**Verification:**
- [ ] Tests backend cubren ambos modos y errores por parametros invalidos.
- [ ] Manual check: cambiar tiempo o FL cambia la respuesta del endpoint cuando corresponde.

**Dependencies:** Tasks 0-1

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/` modulo adaptador/proyeccion vertical nuevo o existente
- `tests/` tests backend de risk map

**Estimated scope:** Medium

#### Task 3: Exponer cross-section real de ruta

**Description:** Crear endpoint de cross-section que reciba ruta y tiempo, y devuelva distancia horizontal, niveles verticales completos y matriz de severidad desde suelo hasta maximo.

**Acceptance criteria:**
- [ ] El endpoint recibe ruta valida y `timeIndex`.
- [ ] La respuesta devuelve eje horizontal, eje vertical completo y matriz de severidad.
- [ ] Errores fuera de dominio o parametros incompletos devuelven mensajes claros.

**Verification:**
- [ ] Tests backend cubren caso valido y caso fuera de dominio.
- [ ] Manual check: una ruta real devuelve una matriz no mock utilizable por el frontend.

**Dependencies:** Tasks 0-1

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/route_profile.py` o adaptador nuevo de serializacion
- `tests/` tests backend de cross-section

**Estimated scope:** Medium

### Checkpoint: Backend Ready

- [ ] `uv run --extra dev pytest` pasa para la nueva cobertura backend.
- [ ] Los tres contratos (`metadata`, `risk-map`, `cross-section`) estan definidos y estables.
- [ ] La semantica vertical coincide con Python.
- [ ] El tamano y formato del payload son aceptables para la primera iteracion del autoplay.

### Phase 2: Frontend Data Wiring and State Model

Objetivo: reemplazar la maqueta actual por una UI que consume la API real y mantiene sincronizados mapa, tiempo, nivel y ruta.

#### Task 4: Introducir cliente API tipado y estado de aplicacion

**Description:** Refactorizar `App.tsx` para extraer fetches, tipos de respuesta y estado compartido de mapa/cross-section/autoplay en una estructura mantenible.

**Acceptance criteria:**
- [ ] El frontend carga metadata del backend al iniciar.
- [ ] El estado contiene `timeIndex`, `riskMode`, `selectedFlightLevelBand`, `route`, `isPlaying` y `isCrossSectionExpanded`.
- [ ] La UI ya no depende de valores mock hardcodeados para el flujo principal.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: la app arranca aun sin errores de tipos.

**Dependencies:** Tasks 0-3

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/` nuevos tipos/clientes/hooks
- `src/frontend/src/index.css`

**Estimated scope:** Medium

#### Task 5: Conectar el mapa a overlays reales y renombrar la app a Aerofrost

**Description:** Reemplazar poligonos mock por el overlay real del endpoint, mostrar el nombre correcto del producto y adaptar controles de modo y FL/franja segun metadata real.

**Acceptance criteria:**
- [ ] La cabecera muestra `Aerofrost`.
- [ ] El mapa deja de usar poligonos mock embebidos.
- [ ] El selector de modo y el selector FL/franja reflejan la metadata recibida.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: cambiar modo y FL/franja actualiza el mapa.

**Dependencies:** Task 4

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/index.css`
- `src/frontend/src/` componentes auxiliares nuevos si hacen falta

**Estimated scope:** Medium

#### Task 6: Activar autoplay temporal real

**Description:** Implementar temporizador real para Play/Pause, ciclo por tiempos disponibles y refresco sincronizado del mapa y, si hay ruta activa, del cross-section.

**Acceptance criteria:**
- [ ] El boton Play avanza automaticamente el `timeIndex`.
- [ ] El boton Pause detiene el avance sin perder el tiempo actual.
- [ ] El cambio temporal refresca mapa y cross-section sin desincronizacion.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: el tiempo avanza solo y se refleja en la UI.

**Dependencies:** Task 4

**Files likely touched:**
- `src/frontend/src/App.tsx`
- posibles hooks auxiliares en `src/frontend/src/`

**Estimated scope:** Small

### Checkpoint: UI Connected

- [ ] `npm run build` pasa en `src/frontend`.
- [ ] El mapa ya no contiene overlays mock.
- [ ] La reproduccion temporal es funcional.
- [ ] El estado de la app responde a datos reales del backend.

### Phase 3: Cross-Section UX and End-to-End Validation

Objetivo: cerrar el flujo completo de seleccion de ruta, corte vertical y ampliacion de la vista.

#### Task 7: Renderizar cross-section real de ruta

**Description:** Sustituir el SVG mock por una visualizacion real del endpoint de cross-section, manteniendo la lectura horizontal por ruta, vertical completa y color por severidad.

**Acceptance criteria:**
- [ ] Seleccionar dos puntos genera una ruta visible y solicita el cross-section real.
- [ ] El panel muestra la matriz de severidad de forma interpretable.
- [ ] Cambiar tiempo con ruta activa refresca el cross-section.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: seleccionar ruta produce corte real, no mock.

**Dependencies:** Tasks 3-6

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/` componente de cross-section nuevo

**Estimated scope:** Medium

#### Task 8: Anadir modo ampliado del cross-section

**Description:** Incorporar un control de ampliar/contraer para el cross-section, manteniendo la misma ruta y datos cargados en una vista mayor y legible.

**Acceptance criteria:**
- [ ] Existe un control visible para ampliar el cross-section.
- [ ] La vista ampliada conserva la ruta activa y el mismo dataset cargado.
- [ ] El usuario puede volver a la vista normal sin perder el estado.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: ampliar y contraer funciona sin recargar la app.

**Dependencies:** Task 7

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/index.css`
- posible componente/modal/panel nuevo

**Estimated scope:** Small

#### Task 9: Validacion end-to-end y documentacion minima

**Description:** Consolidar pruebas, ajustar README si hace falta y verificar que el flujo completo backend + frontend cumple la spec aprobada.

**Acceptance criteria:**
- [ ] Cobertura backend nueva queda integrada en la suite existente.
- [ ] La app compila y el flujo manual principal funciona.
- [ ] La documentacion operativa minima refleja como arrancar backend y frontend con los endpoints reales.

**Verification:**
- [ ] Tests backend: `uv run --extra dev pytest`
- [ ] Build frontend: `npm run build`
- [ ] Manual check: nombre, mapa real, modo generico, modo FL/franja, autoplay, ruta, cross-section ampliable.

**Dependencies:** Tasks 1-8

**Files likely touched:**
- `README.md`
- `tests/` archivos relevantes
- `src/backend/main.py`
- `src/frontend/src/App.tsx`

**Estimated scope:** Medium

### Checkpoint: Complete

- [ ] Todos los criterios de exito de `specs/spec_aerofrost_revision_end_to_end.md` se cumplen.
- [ ] `uv run --extra dev pytest` pasa.
- [ ] `npm run build` pasa en `src/frontend`.
- [ ] El flujo principal funciona end-to-end en revision manual.

## Parallelization Opportunities

- **Paralelizable despues de Task 1:** Task 2 y Task 3, si el contrato de metadata ya fija la semantica vertical.
- **Paralelizable despues de Task 4:** parte visual del mapa (Task 5) y autoplay (Task 6), porque comparten estado pero no el mismo bloque de render principal si se separa en componentes.
- **Secuencial recomendado:** Task 7 antes de Task 8, porque la ampliacion depende de un cross-section ya real.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| La semantica Python de FL/franjas no esta encapsulada aun para consumo web | High | Hacer primero `Task 0` y `Task 1`, crear adapter backend explicito y no construir el selector frontend hasta cerrar esa decision |
| El payload del mapa puede ser demasiado pesado para animacion temporal | High | Medirlo en backend antes del refactor UI; si hace falta, cachear por tiempo/modo o cambiar el formato del overlay antes de conectar autoplay |
| `route_profile.py` hoy esta orientado a artefacto estatico, no a API JSON interactiva | Medium | Reutilizar calculo interno y anadir serializer ligero para endpoint, evitando acoplar la figura PNG a la API |
| El refactor de `App.tsx` puede mezclar demasiadas responsabilidades | Medium | Extraer cliente API, tipos y componente de cross-section antes de ampliar la UI |
| El autoplay puede provocar race conditions de fetch | Medium | Introducir cancelacion o guardas de estado para ignorar respuestas obsoletas |

## Verification Checkpoints

### Checkpoint A: Contratos backend
- [ ] Endpoints definidos
- [ ] Tests de contrato pasando
- [ ] Semantica FL/franjas validada contra Python

### Checkpoint B: Mapa real y autoplay
- [ ] Header `Aerofrost`
- [ ] Sin overlays mock
- [ ] Play/Pause funcional
- [ ] Selector de modo y FL/franja operativo

### Checkpoint C: Flujo de ruta completo
- [ ] Ruta seleccionable en mapa
- [ ] Cross-section real desde suelo hasta maximo
- [ ] Vista ampliada disponible
- [ ] Tiempo sincroniza mapa y corte

## Open Questions

- Elegir el formato final de overlay de mapa mas adecuado para rendimiento y simplicidad del frontend.
- Decidir si se introduce cache backend en memoria en esta iteracion o solo si el rendimiento lo exige durante la implementacion.
