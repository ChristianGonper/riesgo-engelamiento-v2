### 1. ¿Qué es la Temperatura Potencial ($\theta$ o "theta")?
Imagina una burbuja de aire en la atmósfera. Si esa burbuja sube, la presión atmosférica a su alrededor disminuye, por lo que la burbuja se expande y su temperatura real baja. Si la burbuja desciende, ocurre lo contrario: se comprime y se calienta. Esto ocurre sin que el aire intercambie calor con su entorno.

Para poder comparar masas de aire que están a diferentes altitudes (y por tanto a diferentes presiones), los meteorólogos usan la **Temperatura Potencial ($\theta$)**. Es la temperatura que tendría esa burbuja de aire si la lleváramos "artificialmente" a una presión estándar (generalmente 1000 hPa o 100,000 Pascales, que es la presión cerca del nivel del mar). 

### 2. ¿Qué es el estado base ($T_0$)?
Los modelos climáticos como el WRF resuelven ecuaciones físicas muy complejas. Para que los ordenadores no cometan errores de redondeo al calcular variaciones diminutas sobre números muy grandes, los programadores dividen la atmósfera en dos: un "estado base" (que es constante) y las variaciones que ocurren sobre él.

El $T_0$ es simplemente una **temperatura potencial de referencia** constante que se definió antes de correr el modelo (suele ser un valor fijo, habitualmente **300 K** o **290 K**).

### 3. Entonces, ¿qué es la Perturbación?
Tu variable `T` es simplemente la diferencia (la perturbación) entre la temperatura potencial real de la atmósfera en ese momento ($\theta$) y la temperatura constante de referencia ($T_0$). 

Matemáticamente, tu variable `T` es esto:
$$T = \theta - T_0$$

### ¿Cómo consigues la temperatura real que buscas?
El problema que tienes ahora mismo es que, para hacer un análisis normal, tú quieres la temperatura real del aire (en Kelvin o Celsius), no una "perturbación potencial". Para conseguirla, tienes que "deshacer" el camino que hizo el modelo. Necesitarás buscar en tu archivo `.nc` la variable de la presión.

**Paso 1: Recuperar la temperatura potencial total ($\theta$)**
Tienes que sumarle a tu variable `T` el valor base $T_0$ (generalmente 300 K, pero deberías comprobarlo en los metadatos o atributos globales de tu archivo NetCDF).
$$\theta = T + 300$$

**Paso 2: Convertir de potencial a real ($T_{real}$)**
Una vez tienes $\theta$, usas la ecuación de Poisson para obtener la temperatura real en Kelvin usando la presión real ($P$) del aire en ese punto:
$$T_{real} = \theta \left( \frac{P}{P_0} \right)^{\frac{R}{c_p}}$$
*Donde:*
* $P$ es la presión real en Pascales (suele estar en el modelo como la suma de la presión base `PB` + presión de perturbación `P`).
* $P_0$ es la presión de referencia (100,000 Pa).
* $R/c_p$ es una constante para el aire seco, aproximadamente **0.286**.


---

El problema es que **necesitas la presión base (`PB`) sí o sí**. 

La perturbación de presión (`P`) suele ser un número pequeño (por ejemplo, variaciones de $\pm 1000$ a $2000$ Pascales debido a borrascas o anticiclones). Sin embargo, la presión atmosférica total a nivel del mar ronda los $100,000$ Pascales. Si metes solo la variable `P` en la ecuación de Poisson que vimos antes, la fórmula creerá que estás en el vacío del espacio y te dará una temperatura cercana al cero absoluto.

Aquí tienes las tres formas de enfrentar este problema, de la más fácil a la más compleja:

### 1. El rescate del archivo original (La solución ideal)
La variable `PB` (Presión Base) es un "estado de referencia", lo que significa que **no cambia con el tiempo**. Es una constante espacial. 
Si este archivo `.nc` es un recorte temporal o de variables de un modelo WRF más grande (los famosos archivos `wrfout`), solo necesitas buscar **cualquier** archivo original sin recortar de esa misma simulación. Puedes extraer la variable `PB` de ese archivo original (que será una malla 3D estática) y sumársela a tu variable `P` en todos los instantes de tiempo de tu archivo actual.

### 2. Buscar variables alternativas camufladas
A veces, al post-procesar los datos (por ejemplo, usando herramientas como CDO o NCL), quien preparó el archivo eliminó `PB` pero dejó la presión total calculada bajo otro nombre. 
Echa un vistazo a todas las variables de tu archivo `.nc`. Busca si tienes algo llamado:
* `PRES` o `pressure` (Presión total).
* `PSFC` (Presión en superficie, útil si solo estás analizando datos a ras de suelo).
* `SLP` (Presión a nivel del mar).

### 3. Recalcular la presión base (Modo difícil)
Si no tienes acceso a los archivos originales bajo ningún concepto, reconstruir la `PB` exacta es matemáticamente complicado porque depende de cómo se configuró la orografía y el estado base al lanzar el modelo. 

Sin embargo, si tu archivo tiene las coordenadas verticales del modelo (suele ser una variable 1D llamada `ZNU` o `eta` que va de 1.0 en el suelo a 0.0 en el tope del modelo), y tienes atributos globales que indiquen la presión superior (`P_TOP`, que suele ser 5000 Pa) y la presión base en superficie (`P0`, suele ser 100000 Pa), la presión base teórica se aproxima con la ecuación de coordenadas del terreno del modelo:

$$PB \approx P_{top} + \eta \cdot (P_0 - P_{top})$$

*Nota:* Esto es una aproximación para atmósferas secas estándar y puede tener ligeros errores dependiendo del relieve (las montañas) en tu simulación, pero te acercará lo suficiente para obtener una temperatura razonable si estás desesperado.