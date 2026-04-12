Esta práctica va a tratar de calcular un riesgo de engelamiento en aviación. 
Lo primero que nos cuenta nuestro profesor es que para que se dé tiene que haber hidrometeoros en estado líquido y además la temperatura debe estar por debajo cero. 
Nos indica que tomemos como base de datos [wrfout_d01_2015-04-17_18 _00_00_corte.nc](/wrfout_d01_2015-04-17_18_00_00_corte.nc) y también podremos basarnos en un [Paper](/SNP6_SESION_4_pp273_284.pdf) en el que participó el profesor.

El profesor hace primeramente una breve exploración de la base. Nos dice que tenemos variables de tiempo, posición y luego las Q. Tenemos la RAIN que son hidrometeoros precipitables de mayor tamaño y los CLOUD que no son precipitables que son de menor tamaño. 

No obstante, dice que estos dos son de líquidos. Nos dice que habría que encontrar en cada píxel de la malla donde tenemos los hidrometeores líquidos y también la temperatura bajo cero. Importante, la temperatura en la base de datos está en grados Kelvin. 
Luego dice que en cada punto de la malla pues también tenemos una altura, entonces habría que ver a qué altura se daría. 
Dice que podríamos empezar como una primera implementación con ver si hay presencia o no presencia, es decir, si en un punto de la malla en cualquiera de las alturas existe riesgo donde se dé esta coincidencia. 
Y luego dice que a posteriori podríamos ver en qué nivel es, tendríamos que determinar un threshold para ver que haya riesgo de engelamiento o no, sacar rangos de altitud en los que exista, etc. 
También nos dice importante que podríamos empezar con una sola unidad temporal con un objetivo también posterior de ver cómo es esa evolución temporal. 
Nos dice también de hacer pues una representación en el mapa de cómo sería el riesgo, etc. 

El profesor nos empieza a delinear cómo sería lo siguiente, hacer esta suma por niveles e integración para calcular el total de agua en las condiciones. 