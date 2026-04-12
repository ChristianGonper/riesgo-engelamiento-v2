## Problem Statement

El proyecto ya resuelve la mayor parte del objetivo técnico inicial de la primera PRD: valida el dataset WRF, detecta hidrometeoros líquidos, estima riesgo aproximado de engelamiento y calcula una severidad heurística con estructura vertical relativa y evolución temporal. Sin embargo, el resultado actual sigue siendo principalmente un pipeline diagnóstico para desarrollo y no todavía un producto final pensado para comunicación académica o interpretación aeronáutica directa.

Desde la perspectiva del profesor y del usuario final del trabajo, la carencia principal ya no es tanto "si podemos calcular algo", sino "si podemos mostrarlo e interpretarlo de forma convincente". Los PNG actuales son funcionales, pero todavía son mapas o paneles de trabajo: muestran máscaras y fracciones, no un producto cartográfico final que permita identificar de un vistazo dónde está el riesgo, cómo cambia según la capa vertical relevante y qué lectura práctica debería hacerse para una aeronave.

Además, la intención original de las notas de clase apuntaba a algo más cercano a una respuesta final sobre riesgo en el dominio y a determinada altura o rango vertical. El sistema actual trabaja correctamente con niveles del modelo y coordenadas eta relativas, pero todavía no ofrece una presentación pensada para "capas de vuelo" o "rangos verticales de interés" como artefacto principal del usuario. Tampoco existe un mapa final enriquecido con contexto geográfico, leyenda de riesgo interpretable, composición visual cuidada o salidas comparables entre tiempos y capas.

El problema a resolver en esta continuación es, por tanto, transformar el pipeline ya implementado en un producto final más cercano a la expectativa académica: mapas mejores, selección de capas verticales útiles, representación espacial del riesgo/severidad con más contexto, y una narrativa de salida que permita justificar qué significa el riesgo de engelamiento para aeronaves bajo las limitaciones del dataset disponible.

## Solution

La continuación del proyecto se enfocará en una capa de producto final sobre el pipeline ya existente, no en sustituirlo. La solución consistirá en reutilizar los productos robustos y aproximados ya calculados para construir una nueva familia de salidas orientadas a visualización final, interpretación por capas y comunicación académica.

Primero, se añadirá una visualización cartográfica de mayor calidad para el dominio WRF. En lugar de mostrar únicamente una máscara binaria o un panel técnico, el sistema deberá generar mapas con contexto geográfico visible, incluyendo explícitamente fronteras o contornos de países, una simbología más informativa y una composición visual apta para incluirse en una entrega o presentación. El mapa deberá representar, como mínimo, el riesgo aproximado o la severidad heurística para un tiempo seleccionado y, cuando proceda, para una capa vertical o banda relativa concreta.

Segundo, se añadirá una capa de producto orientada a altura o rango vertical de interés para aeronaves. Dado que el dataset no permite altitud geométrica exacta, esta salida deberá presentarse explícitamente como una interpretación por niveles del modelo, bandas eta o rangos relativos, pero organizada de modo que el usuario pueda responder preguntas del tipo: "¿en qué parte del dominio está el mayor riesgo en la banda baja/media/alta?" o "¿qué capa vertical relativa es más problemática en este instante?".

Tercero, se consolidará una salida final de síntesis para el tiempo seleccionado y, opcionalmente, para una pequeña serie temporal de tiempos de interés. Esa salida podrá combinar mapa principal, resumen textual, severidad dominante, banda vertical dominante y notas de interpretación para aeronaves. El resultado debe servir como producto final del trabajo y no solo como artefacto intermedio de ingeniería.

La solución seguirá preservando las limitaciones físicas ya conocidas: no afirmará altitudes exactas si no pueden calcularse, no presentará la severidad como una escala operacional certificada y distinguirá con claridad entre diagnóstico robusto, proxy aproximado y heurística.

## User Stories

1. Como estudiante, quiero partir del pipeline ya construido sin rehacer la lógica física, para poder concentrarme en el producto final del trabajo.
2. Como estudiante, quiero saber con claridad qué partes de la intención inicial del profesor ya están implementadas y cuáles no, para planificar la continuación con criterio.
3. Como estudiante, quiero una salida final más presentable que los PNG técnicos actuales, para poder enseñarla como resultado de la práctica.
4. Como profesor, quiero ver un mapa final interpretable del riesgo de engelamiento, para evaluar rápidamente si el trabajo responde a la pregunta planteada.
5. Como profesor, quiero que el mapa tenga contexto geográfico suficiente, para reconocer dónde se sitúan las zonas de mayor riesgo.
6. Como profesor, quiero que se vean las fronteras o contornos de los países en el mapa final, para ubicar mejor el riesgo sobre el territorio.
7. Como profesor, quiero que la leyenda y la simbología indiquen claramente qué significa cada color o categoría, para no depender del texto técnico del código.
8. Como usuario, quiero ver no solo presencia o ausencia, sino una representación del nivel de riesgo o severidad heurística, para entender mejor la distribución espacial del fenómeno.
9. Como usuario, quiero seleccionar un tiempo concreto para generar el mapa final, para centrar el análisis en un caso representativo.
10. Como usuario, quiero poder generar mapas para varios tiempos destacados, para comparar la evolución del caso.
11. Como usuario, quiero que el mapa final pueda representar la severidad total del dominio o una banda vertical concreta, para responder preguntas más específicas.
12. Como usuario, quiero elegir una banda vertical relativa de interés, para inspeccionar el riesgo en capas bajas, medias o altas del modelo.
13. Como usuario, quiero que el sistema indique qué banda vertical relativa domina el riesgo en cada instante, para interpretar rápidamente la estructura vertical.
14. Como usuario, quiero una tabla o resumen que acompañe al mapa, para ver clase de severidad, cobertura espacial y persistencia sin abrir varios archivos distintos.
15. Como usuario, quiero que el producto final explique explícitamente si está mostrando una máscara binaria, un proxy aproximado o una severidad heurística, para no sobreinterpretar la figura.
16. Como usuario, quiero poder distinguir entre un mapa del riesgo aproximado y un mapa de la severidad heurística, para elegir la salida que mejor responda a mi pregunta.
17. Como usuario, quiero una forma de centrar la interpretación en aeronaves, para traducir el resultado meteorológico a una lectura más aplicada.
18. Como usuario, quiero que el sistema identifique rangos verticales relativos de mayor interés para vuelo, para saber en qué capa del modelo conviene fijarse.
19. Como usuario, quiero que las bandas verticales se describan en un lenguaje legible, para comunicar mejor los resultados aunque no disponga de altura geométrica exacta.
20. Como usuario, quiero que el producto final resuma si el principal riesgo está en banda baja, media o alta, para poder comunicar la conclusión de forma compacta.
21. Como usuario, quiero que el mapa destaque visualmente las áreas de mayor riesgo, para poder localizarlas de un vistazo.
22. Como usuario, quiero que los colores usados transmitan gradación de peligro y no solo categorías binarias, para que la figura sea más informativa.
23. Como usuario, quiero que la salida pueda incluir anotaciones o recuadros de resumen, para que el PNG por sí solo sea más autosuficiente.
24. Como usuario, quiero que el sistema siga exportando formatos máquina-legibles, para poder reutilizar la información en análisis posteriores.
25. Como desarrollador, quiero reutilizar los productos de Phase 5 y Phase 6 como entradas de una capa de visualización final, para no duplicar la física.
26. Como desarrollador, quiero separar claramente el cálculo del riesgo de la composición cartográfica, para mantener el código testeable.
27. Como desarrollador, quiero centralizar paletas, estilos, umbrales visuales y configuración de layout, para poder iterar sobre el diseño sin tocar la lógica científica.
28. Como desarrollador, quiero una interfaz simple para generar mapas finales por tiempo y por banda vertical, para que la CLI siga siendo reproducible.
29. Como desarrollador, quiero introducir un concepto explícito de "producto final" o "vista final", para no seguir mezclando artefactos técnicos y artefactos de presentación.
30. Como desarrollador, quiero que los resúmenes de salida incluyan metadatos suficientes para reconstruir la figura o justificarla, para facilitar validación y trazabilidad.
31. Como desarrollador, quiero pruebas que verifiquen el contenido semántico de los mapas y resúmenes, para evitar regresiones cuando cambie la presentación.
32. Como investigador, quiero una vista espacial de la severidad heurística por dominio, para estudiar no solo cobertura sino intensidad relativa.
33. Como investigador, quiero una vista espacial condicionada por banda vertical, para analizar cómo cambia el riesgo según la estructura relativa del perfil.
34. Como investigador, quiero comparar el mapa del riesgo aproximado con el de severidad heurística, para entender qué añade la heurística.
35. Como investigador, quiero conservar la serie temporal y la estructura vertical actuales como respaldo, para no perder la interpretación diagnóstica detrás del producto final.
36. Como docente, quiero que el trabajo final deje claras las limitaciones de altitud y termodinámica, para que el resultado sea defendible académicamente.
37. Como docente, quiero una salida visual que pueda insertarse casi directamente en una memoria o presentación, para valorar el acabado final del proyecto.
38. Como docente, quiero que la representación final responda mejor a la pregunta práctica de "dónde" y "en qué capa" está el riesgo, para que el ejercicio no se quede en una máscara técnica.
39. Como usuario, quiero que la CLI permita pedir explícitamente la figura final, para no tener que recombinar manualmente artefactos intermedios.
40. Como usuario, quiero una nomenclatura clara entre productos diagnósticos y productos finales, para entender qué archivo debo abrir primero.
41. Como usuario, quiero que la salida final destaque los tiempos más relevantes de la serie, para centrar la interpretación en los momentos de mayor interés.

## Implementation Decisions

- La continuación se apoyará en las salidas ya existentes de validación, Phase 5 y Phase 6, sin reemplazar la lógica física o heurística ya consolidada.
- El nuevo alcance se centrará en producto final, visualización y organización de salidas, no en volver a abrir la discusión básica de `QCLOUD`, `QRAIN`, `T`, `P` o `ZNW`.
- Se mantendrá la distinción entre:
  - diagnóstico robusto,
  - proxy termodinámico aproximado,
  - severidad heurística.
- El sistema incorporará una nueva capa conceptual de visualización final que consuma productos ya calculados y genere figuras de presentación.
- Se definirá una configuración visual explícita para:
  - paletas de color,
  - leyendas,
  - títulos,
  - anotaciones,
  - tamaño y composición de figuras,
  - escalas visuales para riesgo y severidad.
- La visualización final deberá incluir contexto geográfico visible del dominio, incluyendo fronteras o contornos de países claramente reconocibles en la figura final.
- El mapa principal deberá poder representar, al menos:
  - riesgo aproximado total para un tiempo,
  - severidad heurística final para un tiempo,
  - y, opcionalmente, una banda vertical relativa seleccionada.
- Se introducirá un concepto explícito de bandas verticales de interés para presentación final, reutilizando las bandas relativas ya documentadas o ampliándolas si hace falta.
- La representación por bandas deberá presentarse como relativa al modelo o a coordenadas eta, no como altitud exacta, salvo que en una futura iteración se disponga de nuevas variables físicas.
- La CLI deberá permitir solicitar el producto final sin obligar al usuario a inspeccionar varios PNG técnicos por separado.
- La salida final deberá combinar figura y resumen legible, incluyendo severidad dominante, banda dominante, cobertura espacial y notas de interpretación.
- El diseño del producto final deberá priorizar la pregunta de usuario "qué riesgo tendría una aeronave en esta capa/este momento" sobre la mera inspección interna del pipeline.
- La composición cartográfica no debe recalcular campos físicos; debe consumir resultados ya derivados por interfaces estables.
- Si se añaden dependencias cartográficas, se adoptarán solo si aportan un salto claro de calidad visual y permiten mostrar fronteras/contornos de países de forma reproducible en el entorno del proyecto.
- Si no se añaden dependencias cartográficas complejas, el diseño visual deberá seguir mejorando claramente la salida actual mediante estilos, overlays, contornos, etiquetas y composición.
- Se mantendrá una salida técnica completa en NetCDF/JSON para trazabilidad, incluso cuando el foco principal sea el PNG final o el panel de presentación.
- Los conceptos de "banda dominante", "capa de interés" y "riesgo para aeronaves" deberán formularse como interpretación guiada de productos relativos, no como una afirmación operacional certificada.
- La continuación podrá organizarse en módulos profundos y estables, por ejemplo:
  - selección y preparación de capas para producto final,
  - composición cartográfica,
  - resumen interpretativo,
  - configuración visual.
- El trabajo deberá dejar abierta una futura mejora física basada en datasets con `PB`, `PH`, `PHB` o `HGT`, pero esa mejora no es requisito para entregar este producto final.

## Testing Decisions

- Una buena prueba seguirá comprobando comportamiento externo observable y no detalles de implementación del layout.
- Las pruebas del producto final deben validar que, dado un campo ya calculado, la capa de visualización genera la salida esperada sin recalcular la física.
- Las pruebas deben verificar que la selección por banda vertical produce los subconjuntos y metadatos correctos.
- Las pruebas deben verificar que el sistema etiqueta correctamente cuándo una figura representa riesgo aproximado y cuándo representa severidad heurística.
- Las pruebas deben verificar que las salidas finales incluyen metadatos, títulos y nombres consistentes con el tipo de producto solicitado.
- Las pruebas deben verificar que el resumen asociado al mapa contiene los campos interpretativos clave para el usuario.
- Las pruebas deben cubrir casos sin riesgo y con riesgo para asegurar que la visualización final no falla en dominios vacíos o poco activos.
- Las pruebas deben verificar que las figuras finales se generan de forma reproducible desde la CLI.
- Las pruebas deben apoyarse en datasets sintéticos pequeños o productos intermedios controlados, siguiendo el patrón ya existente en el repositorio.
- Los módulos prioritarios a probar serán:
  - selección de producto final por tiempo y banda,
  - composición del resumen final,
  - exportación de artefactos finales,
  - integración CLI para la nueva salida.
- El contenido estético exacto no debe probarse píxel a píxel; debe probarse la semántica observable del producto, sus metadatos y la existencia coherente de los artefactos.

## Out of Scope

- Rehacer desde cero la metodología física del riesgo aproximado ya aceptada en la primera PRD.
- Convertir automáticamente niveles del modelo en altitud geométrica exacta sin disponer de las variables necesarias.
- Presentar la severidad como una escala operativa certificada para aviación real.
- Construir una aplicación web completa o un visor interactivo complejo en esta iteración.
- Validar el producto final contra observaciones de engelamiento en vuelo.
- Resolver plenamente la interpretación operacional por nivel de vuelo real si el dataset sigue sin permitir esa traducción física rigurosa.

## Further Notes

- La exploración realizada sobre el estado actual del repositorio muestra que la intención inicial del profesor está muy avanzada en el plano diagnóstico, pero todavía no en el plano de presentación final.
- Hoy ya existen:
  - validación reproducible del dataset,
  - máscara líquida horizontal,
  - riesgo aproximado de engelamiento,
  - severidad heurística y estructura vertical relativa,
  - salidas Markdown, JSON, NetCDF y PNG.
- La mayor brecha actual es de producto final:
  - mapa más logrado,
  - fronteras de países visibles para orientar la lectura territorial,
  - lectura más orientada a aeronaves,
  - mejor conexión entre severidad espacial y banda vertical de interés,
  - y un artefacto final más defendible en una entrega académica.
- La continuación debería medirse no tanto por añadir otra heurística, sino por convertir el diagnóstico ya construido en una respuesta visual e interpretativa más convincente.
