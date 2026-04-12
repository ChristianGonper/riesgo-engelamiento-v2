# PRD: Riesgo de Engelamiento en Aviacion sobre salida WRF

## Problem Statement

Se necesita construir una solucion reproducible que permita identificar y visualizar riesgo de engelamiento en aviacion a partir de una salida WRF disponible en el repositorio. El objetivo academico y tecnico es empezar desde cero con una primera implementacion util, verificable e incremental, usando como fuente principal el archivo `wrfout_d01_2015-04-17_18_00_00_corte` y las notas de clase y desarrollo incluidas en el proyecto.

El riesgo de engelamiento, desde el punto de vista meteorologico, depende de la coexistencia de hidrometeoros en fase liquida y temperaturas por debajo de cero. Sin embargo, el archivo disponible no incluye la presion base `PB` ni variables de altura geometrica como `PH`, `PHB` o `HGT`, por lo que no es posible reconstruir con rigor completo ni la temperatura real del aire ni la altitud geometrica exacta de cada nivel. Aun asi, el archivo si contiene suficiente informacion para desarrollar una primera solucion incremental basada en presencia de hidrometeoros liquidos, evolucion temporal, distribucion por niveles del modelo y una estimacion aproximada de riesgo.

La necesidad real no es solo generar una figura o un analisis ad hoc, sino establecer una base de trabajo reproducible, documentada y extensible para que futuras iteraciones incorporen severidad, capas verticales, rangos de niveles y analisis temporal mas ricos sin rehacer la arquitectura.

## Solution

La solucion sera un pipeline reproducible en Python que lea la salida WRF, derive variables diagnosticas y produzca productos de analisis incremental en fases.

La primera fase proporcionara una deteccion binaria de presencia de hidrometeoros liquidos por punto horizontal de la malla y por instante temporal, usando `QCLOUD + QRAIN`, junto con visualizaciones y salidas tabulares basicas. Esta fase se considerara fisicamente robusta dentro de las limitaciones del dataset.

La segunda fase anadira analisis vertical relativo sobre los niveles del modelo, usando `bottom_top` y `ZNW`, para identificar en que niveles eta aparece agua liquida, donde coexiste con hielo (`QICE`) y como cambia esa estructura en el tiempo. Esta fase seguira siendo consistente con los datos presentes, aunque no expresara resultados en metros reales.

La tercera y ultima fase del alcance de este PRD estimara un riesgo de engelamiento aproximado, aceptando explicitamente una aproximacion termodinamica por ausencia de `PB`. Se recuperara la temperatura potencial total como `theta = T + 300`, y se definira una estrategia documentada para aproximar la presion total a partir de la coordenada vertical del modelo y parametros de referencia. Con ello se calculara una temperatura real aproximada y una mascara de riesgo potencial de engelamiento. Esta salida debera etiquetarse siempre como estimacion o proxy y no como diagnostico fisico exacto.

Toda la implementacion se desarrollara de forma incremental, con interfaces claras entre lectura de datos, derivacion de variables, logica de diagnostico y representacion de resultados, de modo que cada fase entregue valor por si misma y permita validacion independiente.

## User Stories

1. Como estudiante de meteorologia, quiero cargar la salida WRF disponible sin pasos manuales opacos, para poder repetir el analisis de forma consistente.
2. Como estudiante de meteorologia, quiero inspeccionar rapidamente las variables disponibles y sus dimensiones, para entender que puede calcularse realmente con el archivo.
3. Como analista, quiero obtener una mascara de presencia de hidrometeoros liquidos por celda horizontal, para localizar zonas candidatas a engelamiento.
4. Como analista, quiero distinguir entre agua liquida y hielo presente en la malla, para no confundir regiones con fisica distinta.
5. Como usuario del script, quiero seleccionar un instante temporal concreto, para analizar primero un caso simple y controlado.
6. Como usuario del script, quiero poder procesar toda la serie temporal disponible, para estudiar la evolucion del fenomeno.
7. Como investigador, quiero resumir para cada tiempo si existe o no presencia de liquido en el dominio, para detectar periodos de interes.
8. Como investigador, quiero cuantificar cuantas celdas horizontales presentan liquido en cada tiempo, para comparar la extension espacial del fenomeno.
9. Como investigador, quiero conocer en que niveles del modelo aparece agua liquida, para describir la estructura vertical relativa del evento.
10. Como investigador, quiero detectar coexistencia de agua liquida e hielo por nivel, para identificar posibles regiones de fase mixta.
11. Como investigador, quiero visualizar mapas del dominio para cada tiempo relevante, para interpretar espacialmente los resultados.
12. Como investigador, quiero generar figuras reproducibles desde script, para evitar depender de inspeccion manual en notebooks.
13. Como docente o revisor, quiero que el pipeline documente claramente que magnitudes son exactas y cuales son aproximadas, para evaluar la validez del trabajo.
14. Como desarrollador, quiero que la lectura del NetCDF este encapsulada en un modulo pequeno, para cambiar la fuente de datos sin tocar toda la logica.
15. Como desarrollador, quiero separar la derivacion termodinamica de la logica de riesgo, para poder mejorar la aproximacion sin romper el resto del sistema.
16. Como desarrollador, quiero tener una representacion intermedia de campos diagnosticos, para reutilizarla en mapas, estadisticos y validaciones.
17. Como desarrollador, quiero que el script falle con mensajes claros si faltan variables esperadas, para diagnosticar rapido problemas de datos.
18. Como usuario, quiero que el flujo indique explicitamente si esta trabajando en modo robusto o modo aproximado, para no sobreinterpretar los resultados.
19. Como usuario, quiero obtener una salida binaria de riesgo potencial por celda y tiempo, para usarla como primer producto operativo de la practica.
20. Como usuario, quiero que el riesgo potencial se base en una formula documentada, para poder justificar academicamente la metodologia.
21. Como usuario, quiero un resumen textual del numero de celdas con riesgo potencial por instante, para comparar momentos sin inspeccionar mapas uno a uno.
22. Como usuario, quiero poder exportar resultados intermedios, para revisarlos o reutilizarlos en fases posteriores.
23. Como usuario, quiero saber cuando un tiempo no presenta hidrometeoros liquidos, para no gastar esfuerzo interpretando instantes vacios.
24. Como investigador, quiero disponer de una fase especifica de analisis temporal, para estudiar persistencia, aparicion y desaparicion del riesgo.
25. Como investigador, quiero construir la solucion por entregas pequenas, para validar cada paso antes de anadir complejidad fisica.
26. Como desarrollador, quiero que las heuristicas y constantes fisicas queden centralizadas, para poder cambiarlas de forma controlada.
27. Como desarrollador, quiero registrar supuestos como `T0 = 300 K`, para que el comportamiento del modelo no dependa de conocimiento implicito.
28. Como desarrollador, quiero poder sustituir en el futuro la presion aproximada por una presion real si aparece un dataset mejor, para mejorar precision sin rehacer la arquitectura.
29. Como desarrollador, quiero que los modulos de figuras no contengan logica fisica, para mantener el codigo testeable.
30. Como docente, quiero que el trabajo final explique por que no puede obtenerse un diagnostico exacto con este archivo, para que la limitacion quede explicitamente justificada.
31. Como docente, quiero que el trabajo muestre resultados utiles a pesar de la ausencia de `PB`, para demostrar criterio tecnico y avance incremental.
32. Como investigador, quiero resumir la ocupacion vertical de los hidrometeoros por tiempo, para identificar capas relativas del modelo mas activas.
33. Como investigador, quiero comparar el peso relativo de `QCLOUD` y `QRAIN`, para distinguir nube liquida de lluvia liquida.
34. Como investigador, quiero usar `QICE` como apoyo interpretativo, para reconocer escenarios donde la aproximacion de riesgo de engelamiento debe leerse con cautela.
35. Como usuario del proyecto, quiero una documentacion central que describa entradas, salidas, limites y fases, para poder continuar la implementacion mas adelante.

## Implementation Decisions

- El proyecto se implementara como script reproducible en Python, no como notebook principal.
- La entrada inicial sera exclusivamente el archivo `wrfout_d01_2015-04-17_18_00_00_corte` presente en el repositorio.
- La lectura de datos se hara con `xarray` y debe soportar tanto un instante individual como el conjunto de tiempos disponible.
- La primera familia de diagnosticos robustos se basara solo en variables observables del archivo: `QCLOUD`, `QRAIN`, `QICE`, `T`, `P`, `ZNW`, `XLAT`, `XLONG` y `XTIME`.
- La presencia de hidrometeoros liquidos se definira mediante la combinacion `QCLOUD + QRAIN`.
- La severidad no se inferira en una primera iteracion a partir de un modelo fisico complejo; se dejara como fase incremental posterior dentro del mismo PRD.
- La estructura vertical se expresara inicialmente en niveles del modelo o coordenada eta relativa, no en metros ni en pies.
- La variable `T` se interpretara como perturbacion de temperatura potencial y se recuperara la temperatura potencial total mediante `theta = T + 300`.
- La ausencia de `PB` impide reconstruir presion total exacta y, por tanto, temperatura real exacta. Esta limitacion se documentara como restriccion central del sistema.
- Se acepta una aproximacion para la presion total basada en la coordenada vertical del modelo y parametros de referencia, siempre etiquetando el resultado como estimacion o proxy.
- El riesgo de engelamiento aproximado se definira como coincidencia entre presencia de hidrometeoros liquidos y temperatura aproximada por debajo de cero.
- Los productos del sistema deberan distinguir explicitamente entre:
  - diagnosticos robustos derivados directamente de variables disponibles,
  - diagnosticos aproximados derivados de reconstrucciones termodinamicas.
- La arquitectura se dividira en modulos conceptuales:
  - lectura y validacion de datos,
  - derivacion de variables fisicas y aproximadas,
  - diagnosticos de liquido, hielo y riesgo,
  - agregaciones temporales y verticales,
  - visualizacion y exportacion.
- Se priorizaran interfaces simples y profundas sobre funciones dispersas acopladas a un unico script monolitico.
- Cada fase debera dejar resultados utilizables por si misma:
  - Fase 1: mascara binaria de liquido y mapas base.
  - Fase 2: analisis vertical relativo y evolucion temporal.
  - Fase 3: riesgo de engelamiento aproximado con metodologia documentada.
  - Fase 4: severidad heuristica y rangos de niveles relativos.
- La severidad, cuando se incorpore, se basara en reglas heuristicas documentadas a partir de cantidad de agua liquida, persistencia temporal y contexto de fase mixta, no en una afirmacion de verdad observacional exacta.
- El sistema debera emitir metadatos o etiquetas visibles en resultados para indicar el modo de calculo usado.
- Se evitara acoplar las decisiones de visualizacion a la logica de calculo, para facilitar pruebas y sustitucion de graficos.
- Los umbrales que se introduzcan en fases posteriores deberan declararse como configuracion explicita.
- La implementacion estara preparada para sustituir en el futuro las aproximaciones por calculos fisicamente mas rigurosos si se consigue un archivo con `PB` u otras variables faltantes.

## Testing Decisions

- Una buena prueba validara comportamiento externo observable y no detalles internos de implementacion.
- Las pruebas deben verificar que la lectura del dataset detecta correctamente variables requeridas y reporta de forma clara las ausentes.
- Las pruebas deben verificar que la derivacion de `theta = T + 300` produce valores coherentes con las expectativas fisicas del archivo.
- Las pruebas deben verificar que la mascara de liquido responde correctamente a casos con `QCLOUD`, `QRAIN` o ambos.
- Las pruebas deben verificar que tiempos sin hidrometeoros producen salida vacia sin errores.
- Las pruebas deben verificar que las agregaciones temporales y verticales mantienen dimensiones y coordenadas esperadas.
- Las pruebas deben verificar que los calculos aproximados queden marcados como tales en las estructuras de salida o en los metadatos del pipeline.
- Las pruebas deben verificar que la logica de riesgo aproximado no se ejecute silenciosamente si faltan los parametros necesarios para la aproximacion elegida.
- Las pruebas deben verificar que los modulos de visualizacion aceptan campos ya calculados y no rehacen logica fisica internamente.
- Los modulos a cubrir con pruebas prioritarias seran:
  - validacion de dataset,
  - derivacion de campos liquidos y de hielo,
  - conversion a temperatura potencial total,
  - aproximacion de presion y temperatura real estimada,
  - mascara de riesgo potencial,
  - agregaciones temporales y por nivel.
- El criterio de calidad de prueba sera que un cambio en formulas, umbrales o dimensiones rompa una prueba solo si altera el comportamiento observable esperado.
- No existe por ahora un cuerpo previo de tests en el repositorio; por ello, el proyecto debera definir su propio patron de pruebas modulares y datos sinteticos pequenos para aislar comportamiento.
- Cuando sea viable, deben usarse datasets sinteticos o subconjuntos pequenos para evitar depender de ejecuciones pesadas sobre el archivo completo en todas las pruebas.

## Out of Scope

- Obtener un diagnostico exacto de temperatura real sin aproximaciones.
- Obtener altitud geometrica exacta de los niveles del modelo en metros o pies.
- Validar el riesgo calculado contra observaciones de engelamiento reales o reportes de aeronaves.
- Desarrollar una interfaz web o aplicacion interactiva.
- Generalizar el pipeline a cualquier salida WRF arbitraria desde la primera iteracion.
- Calibrar un modelo fisico completo de severidad con garantias operativas.
- Incluir una fase dependiente de conseguir `PB` desde la fuente original.

## Further Notes

- El archivo actualmente disponible contiene informacion suficiente para analisis espacial, temporal y vertical relativo, pero no para reconstruccion termodinamica exacta.
- En el primer instante temporal no aparecen hidrometeoros, por lo que la implementacion debe soportar tiempos sin senal.
- La metodologia de riesgo aproximado debe documentarse como una decision consciente derivada de las limitaciones del dataset y no como sustitucion silenciosa del calculo exacto.
- La trazabilidad de supuestos fisicos es parte del entregable, no un detalle secundario.
- El exito de esta practica depende tanto de producir resultados utiles como de dejar clara la frontera entre conocimiento derivado directamente de los datos y conocimiento aproximado.
