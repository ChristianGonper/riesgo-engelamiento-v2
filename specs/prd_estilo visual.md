## Problem Statement

Los pilotos, despachadores de vuelo y estudiantes de meteorología aeronáutica necesitan evaluar el riesgo de engelamiento (acumulación de hielo en las aeronaves) en diferentes regiones, altitudes y momentos de tiempo a partir de modelos meteorológicos complejos (archivos WRF). Actualmente, la visualización de estos datos suele ser estática, bidimensional y poco intuitiva. Existe una necesidad crítica de una interfaz interactiva y visualmente avanzada que permita a los usuarios explorar la evolución espacial y temporal del riesgo de engelamiento, así como planificar rutas (cortes transversales) de manera dinámica para tomar decisiones de vuelo seguras.

## Solution

Una aplicación web interactiva dividida en una API backend en Python (FastAPI) y un frontend moderno (React + Vite). La interfaz gráfica actuará como un "centro de control futurista" utilizando la estética "Aero-Frost" (Glassmorphism avanzado). Contará con dos paneles principales:
1. **Panel Espacial (Mapa 2D):** Un mapa interactivo que superpone el riesgo de engelamiento de forma translúcida y codificada por colores (basado en la severidad), controlado por un reproductor temporal y un deslizador de altitud.
2. **Panel de Corte Transversal (Cross-Section):** Un gráfico dinámico 2D que muestra el perfil vertical de la atmósfera entre dos puntos seleccionados interactivamente mediante clics en el mapa, actualizándose según la fase temporal activa.

Todo el diseño UI/UX de esta solución se prototipará y construirá utilizando el **MCP de Pencil** como herramienta de diseño principal antes y durante la codificación.

## User Stories

1. As a user, I want to view a base geographical map with country borders and terrain, so that I have spatial context for the meteorological data.
2. As a meteorologist, I want areas with no icing risk to appear transparent on the map, so that my view of the geography is not unnecessarily obstructed.
3. As a pilot, I want areas with icing risk to be color-coded based on severity (Safe/Green, Caution/Yellow, Severe/Red), so that I can instantly identify dangerous flight zones.
4. As a flight dispatcher, I want to use an altitude slider, so that I can visualize the icing risk at specific flight levels (FL) or pressure heights.
5. As a user, I want to see a timeline control (slider), so that I can manually scrub through different forecast hours.
6. As a user, I want a Play/Pause button for the timeline, so that I can watch an automated animation of the icing risk evolution over time.
7. As a pilot planning a route, I want to click on two distinct points (A and B) on the map, so that I can define a specific flight path.
8. As a pilot, I want the system to automatically generate a vertical cross-section chart after selecting two points, so that I can see the icing risk profile across altitudes for that specific route.
9. As a user, I want the cross-section chart to update automatically when I change the time or altitude sliders, so that the route profile is always synchronized with the global map state.
10. As a design-conscious user, I want the UI panels to have a "frosted glass" effect with dynamic background blurring, so that the application feels like a premium, modern aviation tool.
11. As a user, I want critical warnings (e.g., SEVERE icing) to have a glowing/neon text effect, so that they immediately draw my attention over the dark background.
12. As an aviation enthusiast, I want to see a dynamic NACA airfoil indicator that changes color and thickness based on the maximum risk on the screen, so that I have a quick visual summary of the aerodynamic threat.
13. As a user, I want the application to load data asynchronously without freezing the UI, so that my experience remains smooth even when querying heavy WRF datasets.

## Implementation Decisions

**Arquitectura y Tecnologías:**
- **Frontend:** React, Vite, TypeScript.
- **Estilos:** TailwindCSS (ideal para implementar los filtros de `backdrop-filter`, `saturate`, y colores con opacidad de forma rápida) y módulos CSS customizados para los efectos neón.
- **Librería de Mapas:** `react-leaflet` (Leaflet) o `react-map-gl` (Mapbox) con un base map oscuro (`#080A10`).
- **Gráficos (Cross-section):** `Plotly.js` (vía `react-plotly.js`) o `Recharts` para renderizar el perfil de altura vs lat/lon con interpolación de colores.
- **Backend:** FastAPI (Python) para exponer los datos del modelo WRF existente.
- **Diseño UI:** Se usará **Pencil MCP** explícitamente para iterar sobre el diseño de los paneles "Aero-Frost", posicionamiento absoluto de los sliders y la superposición del perfil alar NACA.

**Módulos Profundos (Deep Modules) a desarrollar:**
1. **`MapOrchestrator` (Frontend):** Módulo que encapsula toda la lógica de Leaflet/Mapbox. Expone una interfaz sencilla para inyectar capas de polígonos/rasters de colores y maneja internamente los eventos de clic (para capturar los Puntos A y B de la ruta) sin filtrar la complejidad de la librería de mapas al resto de la app.
2. **`AeroFrostTheme` (Frontend):** Un sistema de componentes UI (`FrostPanel`, `NeonText`, `GlassButton`) que encapsula la complejidad de los gradientes, sombras (`0 8px 32px 0 rgba(0, 0, 0, 0.37)`), y desenfoques. Cualquier módulo de la app usará estos componentes sin preocuparse por el CSS subyacente.
3. **`WRFDataClient` (Frontend/Backend):** Cliente API que gestiona el estado de caché de los volúmenes 3D solicitados. Evitará pedir el mismo corte transversal dos veces si los puntos y el tiempo no han cambiado.
4. **`CrossSectionEngine` (Backend):** Módulo en Python que recibe `(lat1, lon1)`, `(lat2, lon2)` y `time_idx`, intercepta los datos del archivo NetCDF/WRF (código ya existente en commits previos), interpola la matriz 2D de altura vs distancia, y devuelve un JSON tipado y optimizado para el renderizado en el frontend.

**Especificaciones de Diseño (Aero-Frost):**
- **Fondo:** `#080A10`
- **Paneles:** Fondo `rgba(255, 255, 255, 0.03)`, Borde `rgba(255, 255, 255, 0.1)`, Blur `20px` a `30px`.
- **Alertas:** Verde (`#00E676`), Amarillo (`#FFD600`), Rojo (`#FF1744`), Azul (`#00B0FF`).
- **Tipografía:** `Inter` para estructura UI, `Roboto Mono` para datos de telemetría.

## Testing Decisions

- **Filosofía de Testing:** Se probará el comportamiento externo y la integración de los componentes, no la implementación interna de los estilos o el DOM específico.
- **Módulos a probar (Frontend con Vitest/React Testing Library):**
  - `TimeControl` y `AltitudeControl`: Verificar que al interactuar con los sliders, los callbacks correspondientes emiten los valores correctos de altitud y tiempo.
  - `MapOrchestrator`: Simular dos clics en el mapa y verificar que se despacha el evento de "Ruta seleccionada" con las coordenadas correctas.
- **Módulos a probar (Backend con Pytest):**
  - `CrossSectionEngine`: Verificar que, dados dos puntos conocidos, la API retorna una matriz de datos válida con la forma esperada (Height x Distance) y códigos HTTP 200. Comprobar el manejo de errores si los puntos caen fuera del dominio del WRF (HTTP 400).
- **Prior Art:** Se revisará la suite de tests existente en la carpeta `tests/` del repositorio para mantener la convención (ej. fixtures de datos WRF de prueba).

## Out of Scope

- Procesamiento o ingesta de nuevos modelos WRF en tiempo real (la aplicación consumirá el dataset o datasets pre-cargados en el servidor).
- Soporte para dispositivos móviles (Mobile Responsive): Debido a la densidad de datos, los gráficos de corte transversal y el uso intensivo de WebGL/Filtros, la interfaz se diseñará exclusivamente para pantallas de escritorio (Desktop-first).
- Sistema de usuarios, login o guardado de sesiones en base de datos.
- Exportación de los mapas a PDF o formatos de imagen estáticos (solo visualización en el navegador).

## Further Notes

- El desarrollo visual con **Pencil MCP** será el primer paso antes de implementar los componentes en React, para asegurar que el efecto "Glassmorphism" y la superposición del indicador NACA funcionan armónicamente sobre el mapa.
- Será necesario definir un contrato estricto de API (JSON schema) entre el frontend de React y el backend de FastAPI para transmitir matrices de datos (Raster) de manera eficiente, posiblemente evaluando el uso de formatos binarios ligeros o GeoJSON optimizado si el peso del JSON tradicional se vuelve un cuello de botella en las animaciones.