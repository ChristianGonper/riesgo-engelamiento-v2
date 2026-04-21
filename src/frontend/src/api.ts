export type RiskMode = 'generic' | 'flight-level'

export type TimeOption = {
  index: number
  label: string
}

export type VerticalOption = {
  id: string
  label: string
  kind: string
  etaMin: number | null
  etaMax: number | null
  levelCount: number
}

export type MapMetadata = {
  datasetPath: string
  timeCount: number
  times: TimeOption[]
  riskModes: Array<{ id: RiskMode; label: string }>
  verticalSelection: {
    kind: string
    label: string
    options: VerticalOption[]
  }
  mapBounds: [[number, number], [number, number]]
}

export type RiskMapPayload = {
  timeIndex: number
  timeLabel: string | null
  mode: RiskMode
  verticalOption: string | null
  resolvedVerticalOption: string | null
  bounds: [[number, number], [number, number]]
  gridShape: [number, number]
  severityRange: [number, number]
  overlayImage: string
  latitudes: number[]
  longitudes: number[]
  severityFormula: string
  sourceMetrics: Record<string, string | number | null>
}

export type CrossSectionPayload = {
  selected_time_index: number
  selected_time_label: string | null
  route_start: [number, number]
  route_end: [number, number]
  route_point_count: number
  distance_km_total: number
  distance_km: number[]
  route_lat: number[]
  route_lon: number[]
  vertical_levels: number
  eta_mid: number[]
  profile_shape: [number, number]
  profile: number[][]
  severity_range: [number, number]
  severity_formula: string
  xAxisLabel: string
  yAxisLabel: string
  verticalExtent: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal })
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) {
        detail = payload.detail
      }
    } catch {
      // ignore invalid json error bodies
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export function fetchMapMetadata(signal?: AbortSignal) {
  return getJson<MapMetadata>('/api/map-metadata', signal)
}

export function fetchRiskMap(
  timeIndex: number,
  mode: RiskMode,
  verticalOption: string | null,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({ timeIndex: String(timeIndex), mode })
  if (verticalOption) {
    params.set('verticalOption', verticalOption)
  }
  return getJson<RiskMapPayload>(`/api/risk-map?${params.toString()}`, signal)
}

export function fetchCrossSection(
  params: {
    timeIndex: number
    routeStartLat: number
    routeStartLon: number
    routeEndLat: number
    routeEndLon: number
    routePoints?: number
  },
  signal?: AbortSignal,
) {
  const search = new URLSearchParams({
    timeIndex: String(params.timeIndex),
    routeStartLat: String(params.routeStartLat),
    routeStartLon: String(params.routeStartLon),
    routeEndLat: String(params.routeEndLat),
    routeEndLon: String(params.routeEndLon),
    routePoints: String(params.routePoints ?? 160),
  })
  return getJson<CrossSectionPayload>(`/api/cross-section?${search.toString()}`, signal)
}
