# PRD: Perfil de Engelamiento en Ruta

## Problem Statement

Necesito una representación clara del perfil de engelamiento a lo largo de una ruta entre dos puntos geográficos, donde el eje horizontal sea la distancia acumulada en kilómetros, el eje vertical represente niveles relativos del modelo (eta/bottom_top), y el color exprese la severidad del engelamiento.  
El objetivo principal es comunicar rápidamente el riesgo en formato briefing, manteniendo trazabilidad técnica y consistencia con el pipeline actual.

## Solution

Se incorporará un nuevo entregable de perfil de ruta que:

- tome una ruta definida por dos puntos (`lat/lon` de inicio y fin),
- muestree una transecta con cantidad configurable de puntos,
- construya un eje de distancia acumulada en km,
- proyecte severidad heurística (fase 6) sobre todos los niveles `bottom_top`,
- renderice una figura tipo perfil (distancia x nivel) con escala de color de severidad,
- exporte artefactos en `PNG + JSON + MD`,
- opere para un único `time-index` por ejecución, en línea con el comportamiento actual.

## User Stories

1. Como analista meteorológico, quiero definir una ruta entre dos coordenadas, para evaluar el perfil de engelamiento en ese trayecto.
2. Como usuario de briefing, quiero ver distancia acumulada en km en el eje X, para interpretar fácilmente dónde empieza y termina el riesgo.
3. Como usuario técnico, quiero ver todos los niveles relativos del modelo en el eje Y, para analizar la estructura vertical completa.
4. Como usuario de operaciones, quiero que el color represente severidad heurística, para identificar rápidamente tramos más críticos.
5. Como usuario del CLI, quiero seleccionar un `time-index`, para generar el perfil para un instante concreto.
6. Como usuario del pipeline, quiero que el nuevo producto conserve el patrón de artefactos `PNG + JSON + MD`, para mantener consistencia.
7. Como investigador, quiero conservar metadatos de ruta, tiempo y escala, para trazabilidad y reproducibilidad.
8. Como desarrollador, quiero que el muestreo de ruta esté encapsulado en un módulo profundo y estable, para reutilizarlo en futuros productos.
9. Como desarrollador, quiero separar cálculo de perfil y render, para poder testear comportamiento sin acoplarlo a gráficos.
10. Como revisor, quiero validaciones claras de coordenadas y resolución de muestreo, para evitar ejecuciones ambiguas o inválidas.
11. Como analista, quiero que el perfil sea legible para briefing, para comunicar hallazgos sin requerir explicación extensa.
12. Como usuario avanzado, quiero controlar el número de puntos de la transecta, para balancear precisión y costo computacional.
13. Como usuario de calidad, quiero que errores de ruta fuera de dominio sean explícitos, para entender límites del resultado.
14. Como usuario de auditoría, quiero un resumen en Markdown con interpretación breve y caveats, para documentación rápida.
15. Como consumidor de datos, quiero JSON con matriz y ejes del perfil, para postproceso y comparativas automatizadas.
16. Como mantenedor, quiero que el contrato del artefacto quede explícito, para evitar cambios silenciosos incompatibles.
17. Como equipo de pruebas, quiero tests de integración CLI, para asegurar que los flags generan artefactos correctos.
18. Como equipo científico, quiero tests del cálculo del perfil, para asegurar coherencia de distancia, dimensiones y valores.
19. Como equipo de visualización, quiero tests del render, para asegurar ejes, colorbar y semántica visual correctas.
20. Como usuario final, quiero un resultado confiable y rápido de interpretar, para apoyar decisiones informadas de planificación.

## Implementation Decisions

- Se agrega un nuevo producto de presentación orientado a perfil de ruta (no reemplaza los mapas geográficos existentes).
- La ruta se define por dos puntos geográficos (inicio/fin) y una densidad de muestreo configurable.
- El eje horizontal se construye como distancia acumulada en km a lo largo de la transecta.
- El eje vertical usa niveles relativos del modelo (`bottom_top`/`eta_mid`), no altitud geométrica.
- El campo de color es severidad heurística de fase 6, manteniendo escala y caveats del sistema actual.
- El procesamiento se mantiene en modo de tiempo único por ejecución (`time-index` canónico).
- El diseño modular se divide en módulos profundos:
  - muestreo y geometría de ruta,
  - construcción del perfil severidad-distancia-nivel,
  - composición de resumen/contrato de artefacto,
  - render del perfil para briefing.
- Se mantienen políticas de caveats: producto proxy, bandas/model levels relativos, sin interpretación de altitud exacta.
- Se extiende CLI con flags explícitos para coordenadas de inicio/fin y densidad de muestreo.
- Se conserva compatibilidad con convenciones de nomenclatura y trazabilidad de artefactos del pipeline existente.
- Se prioriza legibilidad visual del briefing por encima de densidad textual en la figura.
- La explicación extensa y trazabilidad detallada se delegan a Markdown/JSON, no al PNG.

## Testing Decisions

- Una buena prueba valida comportamiento externo observable: contrato de entradas/salidas, forma del perfil, semántica de ejes y metadatos.
- No se prueban detalles internos de implementación ni pasos intermedios no contractuales.
- Módulos a cubrir obligatoriamente:
  - integración CLI del nuevo modo perfil de ruta,
  - cálculo de perfil de severidad sobre transecta,
  - render del perfil (ejes, colorbar, título/subtítulo y consistencia visual básica).
- Prior art de pruebas: patrón existente de tests sintéticos en fases 5/6 y producto final, con datasets pequeños y validación de artefactos `PNG + JSON + MD`.
- Criterios mínimos:
  - eje X en km creciente y consistente con origen/destino,
  - eje Y coherente con niveles relativos,
  - matriz de severidad con dimensiones esperadas,
  - artefactos generados con nombres y contrato correctos,
  - errores claros ante parámetros inválidos.
- Los tests deben mantener robustez frente a refactors internos, anclándose en contratos públicos.

## Out of Scope

- Conversión de niveles a altitud geométrica exacta (m/ft) o niveles de vuelo operacionales.
- Diagnóstico operativo certificable de engelamiento.
- Rutas complejas con múltiples waypoints o ingestión de archivos externos en esta iteración inicial.
- Comparativos multi-tiempo en una sola figura como modo principal.
- Interfaz web interactiva.
- Cambios al modelo físico de severidad heurística más allá de su reutilización en el perfil.

## Further Notes

- Este entregable complementa el mapa geográfico: ahora se agrega lectura “a lo largo de ruta”.
- El enfoque mantiene coherencia con las limitaciones ya documentadas del dataset (proxy y vertical relativo).
- La configuración elegida favorece comunicación rápida para briefing sin perder trazabilidad técnica en artefactos adjuntos.