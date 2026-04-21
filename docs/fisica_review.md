# Revisión Física del Pipeline de Riesgo de Engelamiento WRF

A continuación se presenta una revisión detallada de los fundamentos físicos y suposiciones meteorológicas implementadas en el código base, destacando aspectos incorrectos o limitaciones severas que comprometen la validez física de los resultados.

## 1. Fase 2: Diagnóstico Binario de Hidrometeoros (Presencia de líquido)

**Implementación actual:**
La presencia de agua líquida se evalúa estrictamente como `QCLOUD + QRAIN > 0`.

**Inconsistencia Física / Numérica:**
En los modelos numéricos de predicción del tiempo como el WRF, las variables de mezcla (mixing ratios) casi nunca son exactamente cero en todo el dominio debido a la precisión de punto flotante y esquemas de advección (ruido numérico). Valores del orden de $10^{-15}$ kg/kg pueden aparecer, los cuales no representan nubes físicas o lluvia real.
* **Recomendación:** Se debe emplear un umbral físico mínimo (threshold) para considerar la existencia de la nube o lluvia. Por ejemplo, `QCLOUD + QRAIN > 1e-6` kg/kg. Evaluar estrictamente `> 0` sobreestimará irrealmente la presencia horizontal y vertical de nubes líquidas.

## 2. Fase 3/5: Reconstrucción Termodinámica Aproximada

Esta fase contiene las simplificaciones físicas más críticas debido a la ausencia de la Presión Base del Estado (`PB`).

### a) Recuperación de la Presión Total
**Implementación actual:**
Se estima la presión base aproximada realizando una interpolación lineal basada en la coordenada relativa eta (`ZNW`):
`pressure_base = 5000 + eta_mid * (100000 - 5000)`
Luego se estima la presión total: `pressure_proxy = P + pressure_base`.

**Inconsistencia Física:**
Esta fórmula asume implícitamente que la **presión en superficie ($P_{sfc}$) es de 1000 hPa de forma constante en todo el dominio**. Esto ignora por completo la **topografía**. Si el dominio WRF incluye cadenas montañosas o terrenos elevados, la presión real en superficie puede ser de 850 hPa, 700 hPa o menos.
* **Consecuencia:** En zonas elevadas, esta aproximación sobreestimará masivamente la presión del aire en los niveles bajos del modelo. Un error de 100 hPa en la presión introducirá un sesgo de varios grados Celsius en el cálculo subsiguiente de la temperatura, arruinando la validez del pronóstico de la isoterma de 0 °C cerca de montañas.

### b) Recuperación de la Temperatura Total y Temperatura Potencial
**Implementación actual:**
`theta = T + 300` y luego `temperature_proxy = theta * (pressure_proxy / 100000) ** 0.286`.
El riesgo se activa si `temperature_proxy <= 273.15 K`.

**Inconsistencias Físicas:**
1. **Error arrastrado por la presión:** Como la temperatura se deriva usando `pressure_proxy`, el error topográfico mencionado anteriormente se propaga directamente a la temperatura. El modelo subestimará el riesgo en zonas montañosas porque calculará que hace más calor del real (a mayor presión calculada para un mismo `theta`, mayor temperatura).
2. **Falta de límite inferior de temperatura (Superenfriamiento irreal):** El agua líquida no existe a cualquier temperatura bajo cero. Alrededor de los -40 °C ocurre la *congelación homogénea*, donde toda gota de agua pura se congela instantáneamente en hielo. En meteorología aeronáutica, el engelamiento por agua líquida superenfriada es muy raro por debajo de -20 °C y físicamente imposible (a nivel macroscópico en nubes) por debajo de -40 °C. El algoritmo actual marcará riesgo de engelamiento incluso a -60 °C si hubiese un remanente numérico de `QCLOUD`. Se debería limitar el riesgo a un rango, por ejemplo, `-40 °C < T < 0 °C` (o más realista `-20 °C < T < 0 °C`).

## 3. Fase 4/6: Severidad Heurística

**Implementación actual:**
El puntaje heurístico de severidad aumenta en función de varias variables, otorgándole un peso positivo (0.15) a la presencia horizontal de una fase mixta (`mixed_horizontal` = `liquid_3d & ice_3d`).

**Inconsistencia Física (Efecto de Fase Mixta):**
Darle un peso *positivo* (es decir, mayor severidad) a la coexistencia de agua líquida y hielo es físicamente cuestionable en términos de acumulación de engelamiento.
* De acuerdo con el **Efecto Wegener-Bergeron-Findeisen**, en una nube de fase mixta, la diferencia de presión de vapor de saturación hace que los cristales de hielo crezcan rápidamente a expensas de las gotas de agua superenfriada, las cuales se evaporan.
* Esto significa que la glaciación progresiva de la nube a menudo **disminuye** la cantidad de agua líquida superenfriada (SLW) disponible para adherirse a una aeronave. Los peores escenarios de engelamiento ocurren generalmente en zonas sin hielo (como en llovizna engelante o estratocúmulos puramente líquidos). Penalizar (sumar severidad) simplemente porque la celda es de fase mixta choca con este principio termodinámico fundamental de la microfísica de nubes, a menos que el objetivo sea identificar corrientes convectivas fuertes (donde conviven todas las fases por las fuertes updrafts).

## Conclusión

El principal cuello de botella físico de esta implementación es la presunción de una **presión de superficie plana (1000 hPa)**, lo cual invalida térmicamente cualquier aproximación de engelamiento sobre terrenos con relieve. Además, el algoritmo se beneficiaría enormemente de filtrar matemáticamente los valores de `QCLOUD` y `QRAIN` con un límite físico mínimo (> 1e-6) y acotar por debajo la temperatura del agua líquida superenfriada. Finalmente, el peso de severidad otorgado a la fase mixta debería revisarse con respecto a los principios de microfísica.
