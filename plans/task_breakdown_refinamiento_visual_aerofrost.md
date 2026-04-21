# Task Breakdown: Refinamiento visual de Aerofrost

## Phase 1: Base visual y transparencia

## Task 1: Verificar y ajustar transparencia real del overlay

**Description:**
Revisar el flujo que genera y renderiza la imagen del overlay para asegurar que las celdas sin engelamiento se vean transparentes de verdad. El objetivo es confirmar si basta con ajustar la opacidad de `ImageOverlay` en frontend o si hace falta un retoque menor en la generacion PNG del backend.

**Acceptance criteria:**
- [ ] Las zonas con severidad `0` no dejan un color de fondo artificial sobre el mapa.
- [ ] El overlay sigue mostrando correctamente las zonas con engelamiento.
- [ ] No se cambian contratos de API salvo necesidad tecnica demostrada.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Si hay backend: tests pasan con `uv run --extra dev pytest`
- [ ] Manual check: con un tiempo donde haya zonas limpias, el mapa base se ve a traves del overlay sin tinte residual.

**Dependencies:** None

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/riesgo_engelamiento/web_api.py`

**Estimated scope:** Small: 1-2 files

## Task 2: Limpiar copy y jerarquia del panel izquierdo

**Description:**
Actualizar el bloque principal izquierdo para que se perciba como producto real y no como consola tecnica. Mantener el nombre `Aerofrost`, sustituir el subtitulo por el copy aprobado y simplificar el mensaje de estado inicial.

**Acceptance criteria:**
- [ ] El subtitulo pasa a `Plataforma operativa de riesgo de engelamiento`.
- [ ] Desaparece la referencia a `backend Python`.
- [ ] El mensaje inicial deja de decir `Selecciona modo, tiempo y ruta.` y pasa a un texto mas limpio.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: el panel izquierdo conserva identidad visual, pero ya no suena a demo tecnica.

**Dependencies:** Task 1

**Files likely touched:**
- `src/frontend/src/App.tsx`

**Estimated scope:** Small: 1 file

### Checkpoint: Phase 1
- [ ] `npm run build` pasa
- [ ] La transparencia base y el panel izquierdo ya reflejan la nueva direccion visual
- [ ] Revisar antes de seguir con el resto del layout

## Phase 2: Simplificacion de tarjetas y controles

## Task 3: Simplificar la tarjeta superior derecha del perfil

**Description:**
Reformular la tarjeta superior derecha para que priorice `PERFIL` y `Aerodynamic threat`, manteniendo el indicador aerodinamico y el color de severidad, pero eliminando textos tecnicos como `Perfil generico`, `Modo por flight level` y la escala `x / 100`.

**Acceptance criteria:**
- [ ] La tarjeta muestra `PERFIL` como encabezado visual principal.
- [ ] La etiqueta `Aerodynamic threat` queda integrada con la severidad actual.
- [ ] Desaparecen `Perfil generico`, `Modo por flight level` y `x / 100`.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: la tarjeta sigue comunicando severidad, pero con lectura mas limpia y menos tecnica.

**Dependencies:** Task 2

**Files likely touched:**
- `src/frontend/src/App.tsx`

**Estimated scope:** Small: 1 file

## Task 4: Mover `Recalcular archivo` a un control discreto

**Description:**
Sacar el boton principal de recarga del panel izquierdo y recolocarlo como accion compacta en la zona inferior de controles, minimizando su peso visual sin perder funcionalidad.

**Acceptance criteria:**
- [ ] `Recalcular archivo` deja de estar como CTA principal del panel izquierdo.
- [ ] La nueva accion es pequena, discreta y sigue siendo accesible.
- [ ] El flujo de recarga sigue actualizando `status`, `cacheStatus` y `metadata` correctamente.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: pulsar el nuevo control lanza la recarga y la interfaz responde igual que antes.
- [ ] Manual check: el control no se solapa en desktop ni rompe el layout principal.

**Dependencies:** Task 2

**Files likely touched:**
- `src/frontend/src/App.tsx`

**Estimated scope:** Small: 1 file

### Checkpoint: Phase 2
- [ ] `npm run build` pasa
- [ ] La tarjeta derecha y el control de recarga ya tienen el nuevo peso visual
- [ ] El flujo de UI sigue operativo tras los cambios de layout

## Phase 3: Limpieza residual y cierre

## Task 5: Eliminar mensajes tecnicos residuales del panel inferior

**Description:**
Limpiar el copy restante de la banda inferior para quitar frases como `Mapa alimentado por overlay real del backend.` y ajustar los mensajes de estado para que suenen operativos y coherentes con el resto de la UI.

**Acceptance criteria:**
- [ ] Desaparece la frase `Mapa alimentado por overlay real del backend.`.
- [ ] Los mensajes de carga y estado del mapa siguen informando sin tono tecnico innecesario.
- [ ] La UI no mezcla copys tecnicos eliminados con la nueva presentacion visual.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Manual check: la franja inferior comunica estado sin referencias a backend ni overlay real.

**Dependencies:** Task 3, Task 4

**Files likely touched:**
- `src/frontend/src/App.tsx`

**Estimated scope:** Small: 1 file

## Task 6: Validacion final de build, tests y flujo completo

**Description:**
Ejecutar la validacion final del refinamiento visual para asegurar que los cambios cumplen la spec y no introducen regresiones funcionales en mapa, timeline, ruta y cross-section.

**Acceptance criteria:**
- [ ] El frontend compila sin errores.
- [ ] Si hubo cambios backend, la suite relevante pasa.
- [ ] La interfaz cumple todos los criterios de exito definidos en la spec.

**Verification:**
- [ ] Build frontend: `npm run build`
- [ ] Si hubo backend: `uv run --extra dev pytest`
- [ ] Manual check: mapa, timeline, ruta, cross-section y recarga siguen funcionando con la nueva apariencia.

**Dependencies:** Task 5

**Files likely touched:**
- `src/frontend/src/App.tsx`
- `src/frontend/src/index.css`
- `src/riesgo_engelamiento/web_api.py`

**Estimated scope:** Small: 1-3 files

### Checkpoint: Complete
- [ ] Todas las tareas anteriores estan completadas
- [ ] Todos los acceptance criteria de la spec estan cubiertos
- [ ] Listo para implementar o revisar resultados finales
