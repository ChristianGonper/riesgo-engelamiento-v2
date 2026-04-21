import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CircleMarker,
  ImageOverlay,
  MapContainer,
  Polyline,
  TileLayer,
  useMapEvents,
} from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'
import { Maximize2, Minimize2, Pause, Play } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

import {
  fetchCacheStatus,
  fetchCrossSection,
  fetchMapMetadata,
  fetchRiskMap,
  recalculateCache,
  type CrossSectionPayload,
  type CacheStatus,
  type MapMetadata,
  type RiskMapPayload,
  type RiskMode,
} from './api'
import { CrossSectionHeatmap } from './CrossSectionHeatmap'

type Point = [number, number]
type RouteSelection = { p1: Point; p2: Point }

function severityLabel(maxSeverity: number) {
  if (maxSeverity >= 60) return 'SEVERE'
  if (maxSeverity >= 40) return 'HIGH'
  if (maxSeverity >= 20) return 'MODERATE'
  if (maxSeverity > 0) return 'LOW'
  return 'NONE'
}

function severityColor(maxSeverity: number) {
  if (maxSeverity >= 60) return '#FF1744'
  if (maxSeverity >= 40) return '#FF7A18'
  if (maxSeverity >= 20) return '#FFD600'
  if (maxSeverity > 0) return '#00E676'
  return '#7dd3fc'
}

function MapClickHandler({ onRouteChange }: { onRouteChange: (route: RouteSelection) => void }) {
  const [points, setPoints] = useState<Point[]>([])

  useMapEvents({
    click(event) {
      const nextPoints = [...points, [event.latlng.lat, event.latlng.lng] as Point].slice(-2)
      setPoints(nextPoints)
      if (nextPoints.length === 2) {
        onRouteChange({ p1: nextPoints[0], p2: nextPoints[1] })
      }
    },
  })

  return (
    <>
      {points.map((point, index) => (
        <CircleMarker
          key={`${point[0]}-${point[1]}-${index}`}
          center={point}
          radius={6}
          pathOptions={{ color: '#00B0FF', fillColor: '#00B0FF', fillOpacity: 0.9, weight: 2 }}
        />
      ))}
      {points.length === 2 ? <Polyline positions={points} color="#00B0FF" weight={3} /> : null}
    </>
  )
}

function App() {
  const [metadata, setMetadata] = useState<MapMetadata | null>(null)
  const [riskMode, setRiskMode] = useState<RiskMode>('generic')
  const [verticalOption, setVerticalOption] = useState<string>('dominant')
  const [timeIndex, setTimeIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [route, setRoute] = useState<RouteSelection | null>(null)
  const [riskMap, setRiskMap] = useState<RiskMapPayload | null>(null)
  const [crossSection, setCrossSection] = useState<CrossSectionPayload | null>(null)
  const [cacheStatus, setCacheStatus] = useState<CacheStatus | null>(null)
  const [isCrossSectionExpanded, setIsCrossSectionExpanded] = useState(false)
  const [isMapLoading, setIsMapLoading] = useState(false)
  const [isCrossSectionLoading, setIsCrossSectionLoading] = useState(false)
  const [status, setStatus] = useState<string>('Cargando Aerofrost...')
  const [mapError, setMapError] = useState<string | null>(null)
  const [crossSectionError, setCrossSectionError] = useState<string | null>(null)
  const mapRequestId = useRef(0)
  const crossSectionRequestId = useRef(0)
  const mapLoadingRef = useRef(false)
  const crossSectionLoadingRef = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    fetchMapMetadata(controller.signal)
      .then((payload) => {
        setMetadata(payload)
        setVerticalOption(payload.verticalSelection.options[0]?.id ?? 'dominant')
        setStatus('Selecciona modo, tiempo y ruta.')
      })
      .catch((error: Error) => {
        setStatus(error.message)
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetchCacheStatus(controller.signal)
      .then((payload) => setCacheStatus(payload))
      .catch(() => setCacheStatus(null))
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!metadata || !isPlaying || metadata.timeCount <= 1) return undefined
    const timer = window.setInterval(() => {
      if (mapLoadingRef.current || crossSectionLoadingRef.current) return
      setTimeIndex((current) => (current + 1) % metadata.timeCount)
    }, 1400)
    return () => window.clearInterval(timer)
  }, [isPlaying, metadata])

  useEffect(() => {
    if (!metadata) return
    const controller = new AbortController()
    const requestId = mapRequestId.current + 1
    mapRequestId.current = requestId
    mapLoadingRef.current = true
    setIsMapLoading(true)
    setMapError(null)
    fetchRiskMap(timeIndex, riskMode, riskMode === 'flight-level' ? verticalOption : null, controller.signal)
      .then((payload) => {
        if (mapRequestId.current === requestId) {
          setRiskMap(payload)
        }
      })
      .catch((error: Error) => {
        if (error.name !== 'AbortError' && mapRequestId.current === requestId) {
          setMapError(error.message)
        }
      })
      .finally(() => {
        if (mapRequestId.current === requestId) {
          mapLoadingRef.current = false
          setIsMapLoading(false)
        }
      })
    return () => controller.abort()
  }, [metadata, riskMode, timeIndex, verticalOption])

  useEffect(() => {
    if (!route) {
      setCrossSection(null)
      setCrossSectionError(null)
      setIsCrossSectionLoading(false)
      crossSectionLoadingRef.current = false
      return
    }
    const controller = new AbortController()
    const requestId = crossSectionRequestId.current + 1
    crossSectionRequestId.current = requestId
    crossSectionLoadingRef.current = true
    setIsCrossSectionLoading(true)
    setCrossSectionError(null)
    fetchCrossSection(
      {
        timeIndex,
        routeStartLat: route.p1[0],
        routeStartLon: route.p1[1],
        routeEndLat: route.p2[0],
        routeEndLon: route.p2[1],
        routePoints: 160,
      },
      controller.signal,
      )
      .then((payload) => {
        if (crossSectionRequestId.current === requestId) {
          setCrossSection(payload)
        }
      })
      .catch((error: Error) => {
        if (error.name !== 'AbortError' && crossSectionRequestId.current === requestId) {
          setCrossSectionError(error.message)
        }
      })
      .finally(() => {
        if (crossSectionRequestId.current === requestId) {
          crossSectionLoadingRef.current = false
          setIsCrossSectionLoading(false)
        }
      })
    return () => controller.abort()
  }, [route, timeIndex])

  const bounds = useMemo<LatLngBoundsExpression | undefined>(() => {
    const sourceBounds = riskMap?.bounds ?? metadata?.mapBounds
    return sourceBounds as LatLngBoundsExpression | undefined
  }, [metadata, riskMap])

  const currentTimeLabel = metadata?.times[timeIndex]?.label ?? `t${timeIndex.toString().padStart(3, '0')}`
  const threatValue = riskMap?.severityRange[1] ?? 0
  const threatLabel = severityLabel(threatValue)
  const threatColor = severityColor(threatValue)
  const cacheLabel = cacheStatus?.state ?? 'missing'
  const frameStatus = isMapLoading
    ? 'Cargando frame de mapa...'
    : isCrossSectionLoading
      ? 'Actualizando corte de ruta...'
      : route
        ? 'Ruta activa sincronizada con el tiempo.'
        : 'Selecciona dos puntos para obtener el corte vertical.'

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-dark text-white selection:bg-info/30">
      <div className="absolute inset-0 z-0">
        <MapContainer
          bounds={bounds}
          center={[40.4168, -3.7038]}
          zoom={6}
          className="h-full w-full bg-[#080A10]"
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {riskMap ? (
            <ImageOverlay url={riskMap.overlayImage} bounds={riskMap.bounds as LatLngBoundsExpression} opacity={0.86} />
          ) : null}
          <MapClickHandler onRouteChange={setRoute} />
          {route ? <Polyline positions={[route.p1, route.p2]} color="#8BE9FD" weight={4} /> : null}
        </MapContainer>
      </div>

      <div className="absolute inset-x-0 top-0 z-10 h-36 bg-[radial-gradient(circle_at_top,rgba(0,176,255,0.18),transparent_58%)]" />

      <div className="absolute left-8 top-8 z-20 flex w-[350px] flex-col gap-4 rounded-3xl p-6 frost-panel shadow-2xl">
        <div>
          <p className="text-[10px] uppercase tracking-[0.32em] text-info/80">Aeronautical Icing Console</p>
          <h1 className="text-3xl font-semibold tracking-[0.1em]">Aerofrost</h1>
          <p className="mt-2 text-sm text-white/60">Mapa operativo conectado al backend Python para riesgo y corte vertical de ruta.</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-sm text-white/70">
          {status}
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-white/55">
          {cacheStatus ? `${cacheStatus.artifactCount} artefactos cacheados` : 'Cache sin estado'}
        </div>
        <button
          type="button"
          className="rounded-2xl border border-info/30 bg-info/10 px-4 py-3 text-sm text-info transition hover:bg-info/20"
          onClick={async () => {
            try {
              setStatus('Recalculando archivo...')
              const payload = await recalculateCache()
              setCacheStatus(payload.cacheStatus)
              setMetadata(payload.metadata)
              setStatus('Archivo listo.')
            } catch (error) {
              setStatus(error instanceof Error ? error.message : 'Recalculo fallido')
            }
          }}
        >
          Recalcular archivo
        </button>
        <div className="text-xs tracking-[0.18em] text-white/45">CACHE {cacheLabel.toUpperCase()}</div>
      </div>

      <div className="absolute right-8 top-8 z-20 flex h-44 w-80 flex-col gap-3 rounded-3xl p-6 frost-panel shadow-2xl">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-[0.24em] text-white/70">AERODYNAMIC THREAT</span>
          <span
            className="rounded-full border px-3 py-1 text-[10px] font-bold tracking-[0.24em]"
            style={{ borderColor: threatColor, color: threatColor, boxShadow: `0 0 18px ${threatColor}66` }}
          >
            {threatLabel}
          </span>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <svg viewBox="0 0 240 72" className="h-full w-full">
            <path
              d="M6 36 Q 76 2 230 36 Q 76 70 6 36"
              fill={`${threatColor}22`}
              stroke={threatColor}
              strokeWidth={threatValue >= 60 ? 4 : 3}
            />
          </svg>
        </div>
        <div className="flex items-center justify-between text-xs text-white/60">
          <span>{riskMode === 'generic' ? 'Perfil generico' : 'Modo por flight level'}</span>
          <span>{threatValue.toFixed(1)} / 100</span>
        </div>
      </div>

      <div className="absolute bottom-8 right-8 z-20 flex h-[380px] w-[600px] flex-col gap-4 rounded-3xl p-6 frost-panel shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-semibold tracking-[0.24em] text-white/80">ROUTE CROSS-SECTION</p>
            <p className="mt-1 text-xs text-white/55">
              {route ? `${currentTimeLabel} · ${crossSection?.distance_km_total.toFixed(1) ?? '--'} km` : 'Haz clic en dos puntos del mapa'}
            </p>
          </div>
          <button
            type="button"
            className="rounded-full border border-white/10 bg-white/6 p-2 text-white/70 transition hover:bg-white/12"
            onClick={() => setIsCrossSectionExpanded((current) => !current)}
          >
            {isCrossSectionExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
        <div className="min-h-0 flex-1">
          {crossSectionError ? (
            <div className="flex h-full items-center justify-center rounded-xl border border-severe/40 bg-severe/10 text-sm text-severe">
              {crossSectionError}
            </div>
          ) : (
            <div className="relative h-full">
              <CrossSectionHeatmap payload={crossSection} />
              {isCrossSectionLoading ? (
                <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-black/24 text-xs uppercase tracking-[0.24em] text-white/60">
                  Actualizando
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      <div className="absolute bottom-8 left-1/2 z-20 flex w-[720px] -translate-x-1/2 flex-col gap-5 rounded-[28px] p-6 frost-panel shadow-2xl">
        <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4">
          <span className="text-xs tracking-[0.24em] text-white/55">MODE</span>
          <div className="flex gap-2">
            {metadata?.riskModes.map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => setRiskMode(mode.id)}
                className={`rounded-full px-4 py-2 text-xs tracking-[0.18em] transition ${
                  riskMode === mode.id
                    ? 'bg-info text-black shadow-[0_0_18px_rgba(0,176,255,0.35)]'
                    : 'bg-white/8 text-white/70 hover:bg-white/14'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
          <span className="text-right text-xs text-white/45">{riskMap?.resolvedVerticalOption ?? 'all levels'}</span>
        </div>

        {riskMode === 'flight-level' ? (
          <div className="grid grid-cols-[auto_1fr] items-center gap-4">
            <span className="text-xs tracking-[0.24em] text-white/55">FL/BAND</span>
            <select
              value={verticalOption}
              onChange={(event) => setVerticalOption(event.target.value)}
              className="rounded-2xl border border-white/10 bg-black/35 px-4 py-3 text-sm text-white outline-none"
            >
              {metadata?.verticalSelection.options.map((option) => (
                <option key={option.id} value={option.id} className="bg-[#07111f] text-white">
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-white/45">
          <span>
            Cache {cacheStatus?.state ?? 'missing'}{isMapLoading ? ' · mapa' : ''}{isCrossSectionLoading ? ' · corte' : ''}
          </span>
          <span>{cacheStatus?.lastRecalculatedAt ?? 'sin recalculo'}</span>
        </div>

        <div className="grid grid-cols-[auto_auto_1fr] items-center gap-4">
          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/18"
            onClick={() => setIsPlaying((current) => !current)}
          >
            {isPlaying ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" />}
          </button>
          <span className="w-32 text-sm font-medium text-white/80">{currentTimeLabel}</span>
          <input
            type="range"
            min={0}
            max={Math.max((metadata?.timeCount ?? 1) - 1, 0)}
            step={1}
            value={timeIndex}
            onChange={(event) => setTimeIndex(Number(event.target.value))}
            className="aerofrost-range"
          />
        </div>

        <div className="flex items-center justify-between text-xs text-white/50">
          <span>{mapError ?? (isMapLoading ? 'Cargando overlay del tiempo actual.' : 'Mapa alimentado por overlay real del backend.')}</span>
          <span>{frameStatus}</span>
        </div>
      </div>

      {isCrossSectionExpanded ? (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/72 p-10 backdrop-blur-sm">
          <div className="flex h-full w-full max-w-6xl flex-col gap-5 rounded-[32px] p-7 frost-panel shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold tracking-[0.24em] text-white/80">ROUTE CROSS-SECTION · EXPANDED</p>
                <p className="mt-1 text-xs text-white/55">
                  {route ? `${currentTimeLabel} · ${crossSection?.distance_km_total.toFixed(1) ?? '--'} km` : 'Sin ruta activa'}
                </p>
              </div>
              <button
                type="button"
                className="rounded-full border border-white/10 bg-white/6 p-3 text-white/70 transition hover:bg-white/12"
                onClick={() => setIsCrossSectionExpanded(false)}
              >
                <Minimize2 size={18} />
              </button>
            </div>
            <div className="min-h-0 flex-1">
              {crossSectionError ? (
                <div className="flex h-full items-center justify-center rounded-2xl border border-severe/40 bg-severe/10 text-sm text-severe">
                  {crossSectionError}
                </div>
              ) : (
                <CrossSectionHeatmap payload={crossSection} expanded />
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default App
