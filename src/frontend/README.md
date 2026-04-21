# Aerofrost Frontend

Cliente React + TypeScript + Vite para la interfaz interactiva de riesgo de engelamiento.

## Estado actual
- Consume la API FastAPI del backend.
- Muestra overlays de riesgo sobre el mapa.
- Permite cambiar tiempo, modo y banda vertical del mapa.
- Genera cross-sections seleccionando dos puntos sobre el mapa.
- Muestra estado de cache y permite lanzar `Recalcular archivo`.
- La reproducción temporal evita solapar requests mientras hay cargas activas.

## Scripts
- `npm run dev`: arranca el entorno de desarrollo.
- `npm run build`: compila TypeScript y genera `dist/`.
- `npm run preview`: sirve la build local.
- `npm run lint`: ejecuta ESLint.

## Desarrollo local
1. Instala dependencias: `npm install`
2. Arranca el backend en `http://127.0.0.1:8000`
3. Inicia el frontend: `npm run dev`

Por defecto el cliente usa `VITE_API_BASE_URL` o `http://127.0.0.1:8000`.

## Estructura
- `src/App.tsx`: layout principal, estado de app, playback y sincronización con la API.
- `src/api.ts`: contratos TypeScript y llamadas HTTP.
- `src/CrossSectionHeatmap.tsx`: render del perfil vertical.
- `src/index.css`: tema visual y utilidades base.

## Notas
- El modo `flight-level` afecta solo al mapa horizontal.
- El perfil vertical mantiene `surface-to-maximum` y referencias `Bajo / Medio / Alto`.
- La UI asume un dataset activo único servido por el backend actual.
