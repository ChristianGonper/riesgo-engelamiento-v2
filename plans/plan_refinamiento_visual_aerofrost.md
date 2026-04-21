# Implementation Plan: Refinamiento visual de Aerofrost

## Overview
Aplicar una limpieza visual y textual sobre la interfaz principal de `Aerofrost` sin romper el flujo operativo actual. El trabajo se concentra en el layout de `App.tsx`, con una posible correccion puntual en backend para garantizar que el overlay del mapa conserve transparencia real cuando la severidad sea cero.

## Architecture Decisions
- Mantener la arquitectura actual de una sola vista principal en `src/frontend/src/App.tsx`.
  - Rationale: el cambio es de presentacion y copy; no compensa introducir nuevos componentes o rehacer la jerarquia.
- Tratar la transparencia del overlay como un contrato visual backend+frontend, no solo CSS.
  - Rationale: aunque `ImageOverlay` ya soporta opacidad, la limpieza real depende de que la imagen PNG tenga alpha 0 en celdas sin severidad.
- Preservar los datos y tipos existentes de la API (`severityRange`, `overlayImage`, `cacheStatus`) salvo que una verificacion demuestre que la transparencia falla.
  - Rationale: la spec no pide cambio funcional ni de contrato.
- Reducir la prominencia de informacion tecnica sin eliminar indicadores operativos utiles.
  - Rationale: hay que limpiar la UI, pero conservar estados que ayudan a entender carga, tiempo activo y sincronizacion.

## Dependency Graph
`web_api.py` overlay alpha -> `api.ts` payload estable -> `App.tsx` layout/copy/controles -> verificacion visual completa

## Implementation Order
1. Verificar y, si hace falta, ajustar la transparencia real del overlay en backend.
2. Simplificar copy y jerarquia visual del panel izquierdo.
3. Redisenar la tarjeta superior derecha para que muestre un perfil mas simple.
4. Reubicar `Recalcular archivo` como control discreto dentro de la zona de controles inferior.
5. Limpiar textos tecnicos residuales y ajustar estados finales.
6. Validar build, tests y comprobacion manual end-to-end.

## Workstreams

### Workstream 1: Overlay Transparente
- Revisar `_array_to_png_data_url()` en `src/riesgo_engelamiento/web_api.py`.
- Confirmar si el alpha actual (`values > 0.0 => 0.74`, si no `0.0`) ya cumple la spec en runtime.
- Si no cumple visualmente, ajustar generacion PNG o la opacidad usada por `ImageOverlay` en `src/frontend/src/App.tsx`.
- Verificar que no aparezcan halos, fondos falsos ni perdida de informacion en zonas con engelamiento.

### Workstream 2: Limpieza del Panel Izquierdo
- Sustituir el subtitulo tecnico por `Plataforma operativa de riesgo de engelamiento`.
- Reemplazar el estado inicial `Selecciona modo, tiempo y ruta.` por un copy mas limpio y neutral.
- Eliminar el bloque visible de `artefactos cacheados`.
- Decidir si el estado `CACHE ...` se mantiene simplificado, se integra en la barra inferior o se reduce a una etiqueta secundaria discreta.

### Workstream 3: Tarjeta Superior Derecha
- Cambiar la cabecera para priorizar `PERFIL` y la etiqueta `Aerodynamic threat`.
- Mantener la forma/indicador aerodinamico existente, pero simplificar las leyendas inferiores.
- Eliminar la lectura `Perfil generico` / `Modo por flight level` y la escala `x / 100`.
- Conservar color y severidad visual como feedback principal.

### Workstream 4: Control Discreto de Recarga
- Sacar `Recalcular archivo` del panel izquierdo.
- Convertirlo en un control pequeno de icono o etiqueta compacta, cerca del bloque inferior de controles, donde no robe protagonismo.
- Mantener estados de `recalculando`, `listo` y `error` a traves de `status` o feedback visual acotado.
- Evitar que el nuevo control rompa layout en desktop o se solape en pantallas pequenas.

### Workstream 5: Limpieza de Mensajes Tecnicos Residuales
- Eliminar `Mapa alimentado por overlay real del backend.`.
- Revisar `frameStatus` y mensajes de carga para que suenen operativos y no tecnicos.
- Comprobar si `all levels`, `Cache ready/missing`, timestamps o labels ingles/espanol mezclados requieren ajuste menor para coherencia.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| La transparencia ya existe en backend y el problema real es la opacidad global del overlay | Medium | Verificar primero `web_api.py` y `ImageOverlay opacity` antes de tocar contratos o logica |
| Reubicar `Recalcular archivo` deteriora usabilidad o solapa otros controles | Medium | Integrarlo en la banda inferior con tamanos pequenos y validar en viewport reducido |
| Limpiar textos elimina demasiada telemetria visible para depurar | Low | Conservar mensajes de carga/error y estado operativo minimo, pero fuera del protagonismo principal |
| Mezcla de cambios visuales en una sola vista complica revisar regresiones | Medium | Implementar por bloques y verificar despues de cada bloque con build y chequeo manual |

## Parallelization Opportunities
- Se pueden preparar en paralelo:
  - revision backend de transparencia del overlay;
  - propuesta de nuevo copy/layout en `App.tsx`.
- Debe hacerse en secuencia:
  - mover el control de recarga despues de decidir donde queda el estado operativo;
  - validacion final despues de todos los cambios visuales.

## Verification Checkpoints

### Checkpoint A: Base visual
- Confirmar si el overlay ya puede quedar transparente sin cambio de API.
- Confirmar que la nueva jerarquia de copy para panel izquierdo y tarjeta derecha esta cerrada.

### Checkpoint B: Layout funcional
- `npm run build`
- Verificacion manual: la vista principal carga, el mapa responde, el timeline funciona y la UI se ve mas limpia.
- Verificacion manual: el boton discreto de recarga sigue ejecutando el flujo correcto.

### Checkpoint C: Complete
- Si hubo backend: `uv run --extra dev pytest`
- Verificacion manual: sin engelamiento visible, el overlay no deja color de fondo artificial.
- Verificacion manual: desaparecen los textos tecnicos pedidos y no se rompe el cross-section ni la seleccion de ruta.

## Open Questions
- Ninguna bloqueante para pasar a TASKS.
