# Implementation Plan: Cacheado derivado de NetCDF + mejora de cross-section en Aerofrost

## Overview
Vamos a cambiar el flujo actual de Aerofrost para que el backend no recalcule mapa y cross-section en cada peticion. En su lugar, el repositorio trabajara con un NetCDF fijo y un conjunto de derivados precalculados persistidos en disco y reutilizados por la API. El frontend consumira esos derivados ya preparados, y solo forzara una nueva ejecucion cuando el usuario pulse `Recalcular archivo` o cambie el NetCDF activo. En paralelo, mejoraremos la cross-section para que renderice mas rapido, trate correctamente los puntos sin dato como transparentes y muestre referencias visuales `Bajo / Medio / Alto` sin alterar la logica cientifica existente.

## Architecture Decisions
- Persistencia de derivados en disco: el backend generara artefactos cacheados por dataset y tiempo, en vez de recalcular bajo demanda.
- Backend como lector de cache: FastAPI servira metadata, mapa y cross-section desde archivos derivados ya generados o desde una cache en memoria del resultado ya cargado.
- Recalculo explicito: solo un endpoint/accion de administracion recalculara los derivados; el slider temporal no debe disparar ciencia.
- Cross-section desacoplada del selector de mapa: `generic / flight-level` sigue afectando solo al mapa horizontal, no al perfil vertical.
- Etiquetas verticales amigables: la cross-section seguira usando `eta_mid` y toda la fisica actual, pero mostrara ayudas visuales `Bajo / Medio / Alto` sobre el eje o la rejilla.
- No-data transparente: tanto mapa como cross-section deben distinguir `sin riesgo` de `sin dato`.

## Dependency Graph
```text
NetCDF fijo en repo
    |
    +-- Pipeline de precalculo persistido
    |       |
    |       +-- manifiesto/cache metadata
    |       +-- overlays de mapa por tiempo/modo/banda
    |       +-- matrices de cross-section reutilizables o datos base 3D
    |
    +-- API FastAPI
    |       |
    |       +-- endpoint metadata/cache-status
    |       +-- endpoint risk-map desde cache
    |       +-- endpoint cross-section desde cache/base derivada
    |       +-- endpoint recalculate/change-dataset
    |
    +-- Cliente frontend tipado
            |
            +-- estado app + estado de cache
            +-- mapa central
            +-- timeline/playback
            +-- cross-section optimizada
```

## Phase 1: Contrato de cache y control del dataset

## Task 1: Definir el modelo de artefactos precalculados
**Description:** Diseñar el contrato de archivos derivados que el backend generara y reutilizara para un NetCDF fijo: manifiesto del dataset activo, metadata temporal, overlays 2D por tiempo/modo/banda y base necesaria para cross-section sin recalculo cientifico repetido.

**Acceptance criteria:**
- [ ] Queda definido un manifiesto estable con dataset activo, version de cache y tiempos disponibles.
- [ ] Queda definida la estrategia de almacenamiento para mapa y cross-section reutilizable.
- [ ] Queda claro que `generic / flight-level` afecta solo al mapa y no al perfil vertical.

**Verification:**
- [ ] Revision manual del contrato propuesto contra `src/riesgo_engelamiento/web_api.py` y `src/riesgo_engelamiento/route_profile.py`
- [ ] El contrato evita recalculo cientifico en `time slider`
- [ ] El plan de nombres/rutas de archivos es consistente y trazable

**Dependencies:** None

**Files likely touched:**
- `src/riesgo_engelamiento/web_api.py`
- `src/riesgo_engelamiento/config.py`
- `docs/` o `plans/`

**Estimated scope:** Small

## Task 2: Diseñar el flujo de recálculo explícito
**Description:** Definir el flujo backend para `Recalcular archivo` y para cambio de NetCDF activo, incluyendo invalidacion de cache, reconstruccion de derivados y estado observable desde frontend.

**Acceptance criteria:**
- [ ] Existe contrato para accion `recalculate` sin ambiguedad.
- [ ] Existe contrato para cambio de dataset activo.
- [ ] El frontend puede saber si los derivados estan listos, recalculando o invalidos.

**Verification:**
- [ ] Revisión manual del flujo de estados
- [ ] Queda definido el comportamiento si falta cache al arrancar
- [ ] Queda definido el comportamiento si el usuario cambia de archivo

**Dependencies:** Task 1

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/config.py`
- `src/frontend/src/api.ts`

**Estimated scope:** Small

### Checkpoint: Foundation Contract
- [ ] El modelo de cache esta cerrado
- [ ] El flujo `dataset activo / recalcular` esta cerrado
- [ ] No hay dependencias cientificas sin definir

## Phase 2: Backend de precálculo y lectura desde cache

## Task 3: Implementar servicio de cache persistida
**Description:** Crear el modulo backend que genera y lee derivados persistidos a partir del NetCDF fijo: metadata, severidad 3D/base reutilizable, overlays de mapa y material necesario para cross-section.

**Acceptance criteria:**
- [ ] Existe un servicio unico de lectura/escritura de cache.
- [ ] El servicio permite consultar si un dataset ya fue precalculado.
- [ ] El servicio evita abrir y recalcular el NetCDF en cada request normal.

**Verification:**
- [ ] Tests backend del servicio de cache
- [ ] Manual check: primer calculo genera archivos; segunda lectura reutiliza cache
- [ ] El tiempo de respuesta de lecturas repetidas baja claramente frente al flujo actual

**Dependencies:** Tasks 1-2

**Files likely touched:**
- `src/riesgo_engelamiento/` nuevo modulo de cache
- `src/riesgo_engelamiento/config.py`
- `tests/`

**Estimated scope:** Medium

## Task 4: Mover `map-metadata` y `risk-map` a lectura desde cache
**Description:** Adaptar la API para que metadata y overlays de mapa se sirvan desde artefactos precalculados, manteniendo el contrato actual o uno muy cercano.

**Acceptance criteria:**
- [ ] `GET /api/map-metadata` deja de recalcular Phase 6 en caliente.
- [ ] `GET /api/risk-map` sirve resultados desde cache persistida.
- [ ] Si no hay cache valida, la API responde con estado claro o instruccion de recalculo.

**Verification:**
- [ ] Tests backend para metadata y risk-map con cache hit/miss
- [ ] Manual check: cambiar tiempo o banda no recalcula ciencia
- [ ] Payload mantiene transparencia donde no hay señal

**Dependencies:** Task 3

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/web_api.py`
- `tests/test_backend_api.py`

**Estimated scope:** Medium

## Task 5: Mover `cross-section` a lectura sobre base reutilizable
**Description:** Adaptar el endpoint de cross-section para que use datos ya precalculados o una base 3D cargada desde cache, sin recomputar severidad completa por cada ruta.

**Acceptance criteria:**
- [ ] `GET /api/cross-section` no vuelve a ejecutar Phase 5/6 para cada cambio de tiempo/ruta.
- [ ] El endpoint sigue devolviendo perfil completo `surface-to-maximum`.
- [ ] El endpoint incluye metadata visual para bandas `Bajo / Medio / Alto` sin alterar formulas.

**Verification:**
- [ ] Tests backend cubren lectura de cross-section desde cache/base derivada
- [ ] Manual check: varias rutas seguidas responden mas rapido que el flujo actual
- [ ] Manual check: el payload trae informacion suficiente para pintar etiquetas amistosas

**Dependencies:** Task 3

**Files likely touched:**
- `src/backend/main.py`
- `src/riesgo_engelamiento/route_profile.py`
- `src/riesgo_engelamiento/web_api.py`
- `tests/test_backend_api.py`

**Estimated scope:** Medium

### Checkpoint: Backend Ready
- [ ] `uv run --extra dev pytest` pasa
- [ ] Metadata, mapa y cross-section leen desde cache o fallan de forma controlada
- [ ] El backend solo recalcula bajo accion explicita

## Phase 3: Control operacional desde frontend

## Task 6: Añadir estado de cache/dataset al cliente frontend
**Description:** Extender el cliente API y el estado React para conocer dataset activo, estado de cache, ultima fecha de recálculo y acciones disponibles.

**Acceptance criteria:**
- [ ] El frontend carga estado de dataset/cache al iniciar.
- [ ] Existe feedback visual de `listo / recalculando / no disponible`.
- [ ] El flujo principal ya no asume calculo inmediato por request.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: la UI muestra estado de cache coherente
- [ ] Cambios de tiempo no bloquean la app con recomputos largos

**Dependencies:** Tasks 4-5

**Files likely touched:**
- `src/frontend/src/api.ts`
- `src/frontend/src/App.tsx`

**Estimated scope:** Small

## Task 7: Añadir botón `Recalcular archivo` y flujo de cambio de NetCDF
**Description:** Incorporar en frontend el control para lanzar el recalculo y, si se desea, seleccionar otro NetCDF disponible, invalidando y regenerando cache.

**Acceptance criteria:**
- [ ] Existe boton visible `Recalcular archivo`.
- [ ] El usuario recibe estado de progreso y resultado del recalculo.
- [ ] El cambio de dataset invalida y recarga metadata/mapa/cross-section de forma limpia.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: pulsar recalcular actualiza el estado y repuebla la UI al terminar
- [ ] Manual check: cambiar dataset no deja residuos del anterior

**Dependencies:** Task 6

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/api.ts`
- `src/backend/main.py`

**Estimated scope:** Medium

### Checkpoint: UI Operational Control
- [ ] El usuario puede operar con cache sin tocar la linea temporal
- [ ] Existe accion manual de recalculo
- [ ] La app refleja correctamente dataset activo y disponibilidad

## Phase 4: Cross-section rápida, transparente y más legible

## Task 8: Corregir semántica visual de no-data en cross-section
**Description:** Ajustar el payload y el render para que puntos sin dato sean transparentes y no hereden un color erroneo; separar claramente `sin dato` de `sin riesgo`.

**Acceptance criteria:**
- [ ] La cross-section no pinta nodata en morado ni con color de riesgo.
- [ ] `0 riesgo` y `nodata` se representan distinto.
- [ ] El rango de severidad visible ignora celdas nodata.

**Verification:**
- [ ] Tests backend/frontend del tratamiento de nodata
- [ ] Manual check: zonas sin nivel o sin dato se ven transparentes
- [ ] Manual check: las zonas con nube/riesgo conservan color correctamente

**Dependencies:** Tasks 5-7

**Files likely touched:**
- `src/riesgo_engelamiento/web_api.py`
- `src/frontend/src/api.ts`
- `src/frontend/src/CrossSectionHeatmap.tsx`

**Estimated scope:** Medium

## Task 9: Optimizar el render del cross-section
**Description:** Sustituir o refactorizar el render SVG actual para evitar miles de nodos por frame y reducir el coste al cambiar tiempo o ampliar el panel.

**Acceptance criteria:**
- [ ] El render del perfil deja de depender de miles de `<rect>` SVG por actualizacion.
- [ ] La vista expandida no duplica trabajo innecesario.
- [ ] El cambio temporal se siente claramente mas fluido.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: scrubbing temporal y autoplay se perciben mas suaves
- [ ] Manual check: expandir/contraer no introduce parpadeos ni retrasos notorios

**Dependencies:** Task 8

**Files likely touched:**
- `src/frontend/src/CrossSectionHeatmap.tsx`
- `src/frontend/src/App.tsx`

**Estimated scope:** Medium

## Task 10: Añadir referencias `Bajo / Medio / Alto` en la cross-section
**Description:** Enriquecer la cross-section con marcadores o bandas visuales amistosas `Bajo / Medio / Alto`, manteniendo `SFC / MAX` y sin convertir esto en altitudes fisicas reales.

**Acceptance criteria:**
- [ ] La cross-section conserva el perfil vertical completo actual.
- [ ] Aparecen referencias visuales `Bajo / Medio / Alto` comprensibles para el usuario.
- [ ] No se altera la semantica cientifica ni se presentan como flight levels reales.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: las etiquetas son visibles y utiles
- [ ] Manual check: no inducen a pensar que son FL exactos

**Dependencies:** Task 8

**Files likely touched:**
- `src/frontend/src/CrossSectionHeatmap.tsx`
- `src/frontend/src/App.tsx`
- opcionalmente `src/riesgo_engelamiento/web_api.py`

**Estimated scope:** Small

### Checkpoint: Cross-Section Improved
- [ ] No-data transparente
- [ ] Render fluido
- [ ] Etiquetas `Bajo / Medio / Alto` visibles
- [ ] La cross-section sigue siendo independiente del selector del mapa

## Phase 5: Timeline, sincronización y validación final

## Task 11: Ajustar autoplay y peticiones para no saturar el backend
**Description:** Revisar la reproduccion temporal para que no genere solapes innecesarios ni intente avanzar mas rapido de lo que la UI puede consumir desde cache.

**Acceptance criteria:**
- [ ] El autoplay no desencadena tormenta de peticiones.
- [ ] Mapa y cross-section se actualizan de forma estable.
- [ ] El estado de carga del frame actual es visible o implícitamente estable.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: al recorrer la linea temporal no aparecen frames “viejos” ni estados inconsistentes
- [ ] Manual check: el tiempo sigue funcionando con ruta activa

**Dependencies:** Tasks 7-10

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/api.ts`

**Estimated scope:** Small

## Task 12: Validación end-to-end y endurecimiento de tests
**Description:** Consolidar pruebas backend y validaciones manuales del flujo completo con dataset cacheado, recalculo explicito, mapa fluido y cross-section correcta.

**Acceptance criteria:**
- [ ] Hay cobertura para cache hit/miss, recalculate y cambio de dataset.
- [ ] Hay cobertura para nodata transparente y contrato de cross-section.
- [ ] El flujo principal queda validado de extremo a extremo.

**Verification:**
- [ ] Tests backend: `uv run --extra dev pytest`
- [ ] Build frontend: `npm run build`
- [ ] Manual check: abrir app, cargar cache, mover tiempo, activar ruta, expandir cross-section, recalcular archivo

**Dependencies:** Tasks 4-11

**Files likely touched:**
- `tests/test_backend_api.py`
- `tests/test_route_profile.py`
- posibles tests frontend si se añaden

**Estimated scope:** Medium

### Checkpoint: Complete
- [ ] El sistema usa cache persistida del NetCDF
- [ ] Solo recalcula con accion explicita
- [ ] El mapa responde rapido al tiempo y banda
- [ ] La cross-section no muestra morado por nodata
- [ ] La cross-section muestra `SFC / MAX` y referencias `Bajo / Medio / Alto`
- [ ] No se ha tocado la fisica ni las formulas meteorologicas

**Riesgos y mitigaciones**
- `Cache demasiado grande en disco` | High | Guardar derivados minimos y versionar el manifiesto; evitar persistir duplicados innecesarios
- `Confusion entre bandas relativas y flight levels reales` | High | Renombrar/explicar mejor en UI y en payload; no vender `Bajo/Medio/Alto` como FL exactos
- `Cross-section aun lenta por muestreo de ruta` | Medium | Reutilizar severidad base ya cargada y optimizar render en frontend
- `Datos sin valor siguen mezclados con riesgo bajo` | High | Introducir semantica nodata explicita en payload y render
- `Cambio de dataset deja cache inconsistente` | Medium | Incluir dataset id/hash en manifiesto y en rutas de cache

**Oportunidades de paralelización**
- Paralelo seguro tras cerrar el contrato:
  - backend de cache persistida;
  - diseño del flujo frontend de estado/cache;
  - pruebas de contrato backend.
- Secuencial recomendado:
  - definir primero contrato de cache y endpoints;
  - luego wiring frontend;
  - despues optimizacion del heatmap.
- Necesita coordinacion:
  - semantica exacta de `nodata`;
  - contrato de `recalculate/change dataset`;
  - labels `Bajo / Medio / Alto`.

**Open Questions**
- Quieres que el artefacto cacheado viva dentro de `outputs/` o prefieres una carpeta dedicada tipo `cache/derived/` para separar entregables de productos operativos.
- Para “cambiar el archivo de NetCDF”, quieres selector de archivos ya existentes en el repositorio o tambien subida manual de un nuevo archivo desde la UI.
- El boton `Recalcular archivo`, quieres que recalculte solo el dataset activo o que rehaga todos los tiempos y todos los derivados de una vez.
- En la cross-section, `Bajo / Medio / Alto` prefieres que aparezca como texto fijo en el eje vertical o como tres franjas sutiles de fondo.

Mi recomendacion por defecto:
1. `cache/derived/` separado de `outputs/`
2. selector de datasets ya presentes en repo, no upload en esta iteracion
3. `Recalcular archivo` rehace todos los tiempos del dataset activo
4. `Bajo / Medio / Alto` como marcas de eje y lineas horizontales sutiles