# Plan: Aero-Frost Visual Style & Interactive UI

> Source PRD: specs/prd_estilo visual.md

## Architectural decisions

Durable decisions that apply across all phases:
- **Backend**: FastAPI wrapper around the existing `riesgo_engelamiento` data pipeline.
- **Frontend**: React + Vite + TypeScript.
- **Styling**: TailwindCSS (for glassmorphism filters, overlays) + custom CSS modules for neon glows.
- **Mapping Engine**: `react-leaflet` over dark tiles.
- **Charting Engine**: `react-plotly.js` or `recharts` for the cross-section.
- **Data Transfer**: Standard JSON (unless bottlenecks occur, in which case we will revisit).
- **Tooling**: Pencil MCP for prototyping the UI layout before implementation.

---

## Phase 1: Prototipado Visual (Pencil MCP)

**User stories**: 10, 11, 12

### What to build
Utilizar Pencil MCP para diseñar el estilo "Aero-Frost", incluyendo:
- Layout general (fondo oscuro, paneles glassmorphism translucidos con blur).
- Controles flotantes (reproductor de tiempo, slider de altitud).
- Panel inferior o lateral para el Cross-Section.
- Diseño del indicador alar NACA y textos tipo "Neon" para las alertas.

### Acceptance criteria
- [ ] Documento `.pen` creado con el layout de la aplicación completa.
- [ ] Componentes base de diseño (FrostPanel, NeonText, GlassButton) visualmente definidos.

---

## Phase 2: Inicialización del Proyecto (FastAPI & React)

**User stories**: 1, 10

### What to build
Configurar el monorepo (o carpetas separadas `backend` y `frontend`). Instalar FastAPI, Uvicorn en el backend; React, Vite, Tailwind, Leaflet en el frontend. Implementar la estructura UI básica con el tema Aero-Frost (fondo negro, paneles vacíos).

### Acceptance criteria
- [ ] Servidor FastAPI levantado y respondiendo en un endpoint de healthcheck `/api/health`.
- [ ] Aplicación React montada mostrando un fondo oscuro y un mapa base Leaflet sin datos.
- [ ] Variables de TailwindCSS configuradas para el diseño glassmorphism.

---

## Phase 3: Visualización 2D Espacial y Controles (Slider)

**User stories**: 2, 3, 4, 5, 6, 13

### What to build
Implementar la carga de la capa espacial de riesgo de engelamiento desde FastAPI al mapa (Leaflet). Añadir el reproductor de tiempo y el slider de altitud. Las áreas sin riesgo deben ser transparentes y las áreas con riesgo usar la escala verde/amarillo/rojo. 

### Acceptance criteria
- [ ] Endpoint `/api/risk-map` que devuelve GeoJSON o raster codificado para una (altitud, tiempo) específica.
- [ ] Sliders de altitud y tiempo funcionales en el UI.
- [ ] El mapa se actualiza asíncronamente al cambiar el slider de altitud o tiempo (Play/Pause automatizado).

---

## Phase 4: Motor de Cross-Section (Corte Transversal)

**User stories**: 7, 8, 9

### What to build
Habilitar clics en el mapa (Punto A y Punto B). Enviar estas coordenadas al backend (`CrossSectionEngine`) que las interpolará sobre el NetCDF/WRF (basado en el código ya existente en `route_profile.py`) y devolverá una matriz 2D (Altura vs Distancia). Renderizar la gráfica de Plotly/Recharts en el Panel inferior con estilo Frost.

### Acceptance criteria
- [ ] El usuario puede hacer clic en dos puntos del mapa y ver una línea de ruta seleccionada.
- [ ] Endpoint `/api/cross-section` recibe (lat1, lon1, lat2, lon2, time) y retorna los datos interpolados 2D.
- [ ] El gráfico de corte transversal se dibuja correctamente en el panel (Plotly/Recharts) con colores mapeados a severidad.
- [ ] El gráfico se actualiza si cambian los sliders de tiempo.

---

## Phase 5: Pulido Visual e Indicador NACA

**User stories**: 11, 12

### What to build
Implementar el componente dinámico del perfil alar NACA, que reacciona visualmente al nivel de riesgo máximo actual mostrado en pantalla. Pulir los efectos de neón para niveles de alerta (ej. SEVERE) sobre el mapa y cross-section.

### Acceptance criteria
- [ ] Gráfico del perfil NACA integrado y conectado al estado global de severidad.
- [ ] Efectos de resplandor (glowing text) y desenfoque (blur) ajustados finamente.
- [ ] Testing End-to-End básico y pruebas unitarias de los módulos principales (Frontend/Backend).
