import type { CrossSectionPayload } from './api'

type CrossSectionHeatmapProps = {
  payload: CrossSectionPayload | null
  expanded?: boolean
}

function colorForSeverity(value: number) {
  const clamped = Math.max(0, Math.min(100, value))
  const hue = 220 - clamped * 2.2
  const lightness = 22 + clamped * 0.22
  return `hsl(${hue} 88% ${lightness}%)`
}

function isNoData(value: number) {
  return Number.isNaN(value) || value < 0
}

export function CrossSectionHeatmap({ payload, expanded = false }: CrossSectionHeatmapProps) {
  if (!payload) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-white/10 bg-black/40 text-sm tracking-[0.18em] text-white/45">
        SELECCIONA 2 PUNTOS EN EL MAPA
      </div>
    )
  }

  const rows = payload.profile.length
  const columns = payload.profile[0]?.length ?? 0
  const width = expanded ? 960 : 520
  const height = expanded ? 520 : 260
  const leftPadding = 60
  const bottomPadding = 34
  const topPadding = 12
  const innerWidth = width - leftPadding - 12
  const innerHeight = height - bottomPadding - topPadding
  const cellWidth = columns > 0 ? innerWidth / columns : innerWidth
  const cellHeight = rows > 0 ? innerHeight / rows : innerHeight
  const bands = payload.visualBands ?? []

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between text-xs text-white/60">
        <span>{payload.selected_time_label ?? `t${payload.selected_time_index}`}</span>
        <span>{payload.distance_km_total.toFixed(1)} km</span>
      </div>
      <div className="rounded-xl border border-white/10 bg-black/45 p-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full">
          <rect x="0" y="0" width={width} height={height} fill="rgba(4, 9, 18, 0.92)" rx="16" />
          {bands.map((band, index) => {
            const bandHeight = innerHeight * (band.end - band.start)
            const y = topPadding + innerHeight - innerHeight * band.end
            return (
              <g key={`${band.label}-${index}`}>
                <rect x={leftPadding} y={y} width={innerWidth} height={bandHeight} fill="rgba(255,255,255,0.025)" />
                <text x={width - 18} y={y + 14} fill="rgba(255,255,255,0.5)" fontSize="10" textAnchor="end">
                  {band.label}
                </text>
              </g>
            )
          })}
          {payload.profile.map((row, rowIndex) =>
            row.map((value, columnIndex) => {
              if (isNoData(value)) {
                return null
              }
              const x = leftPadding + columnIndex * cellWidth
              const y = topPadding + rowIndex * cellHeight
              return (
                <rect
                  key={`${rowIndex}-${columnIndex}`}
                  x={x}
                  y={y}
                  width={Math.max(cellWidth + 0.5, 1)}
                  height={Math.max(cellHeight + 0.5, 1)}
                  fill={colorForSeverity(value)}
                />
              )
            }),
          )}

          <line x1={leftPadding} y1={topPadding} x2={leftPadding} y2={topPadding + innerHeight} stroke="rgba(255,255,255,0.35)" />
          <line x1={leftPadding} y1={topPadding + innerHeight} x2={leftPadding + innerWidth} y2={topPadding + innerHeight} stroke="rgba(255,255,255,0.35)" />

          <text x="18" y={topPadding + 10} fill="rgba(255,255,255,0.72)" fontSize="10">MAX</text>
          <text x="22" y={topPadding + innerHeight} fill="rgba(255,255,255,0.72)" fontSize="10">SFC</text>
          <text x={leftPadding} y={height - 8} fill="rgba(255,255,255,0.72)" fontSize="10">0 km</text>
          <text x={leftPadding + innerWidth - 42} y={height - 8} fill="rgba(255,255,255,0.72)" fontSize="10">
            {payload.distance_km_total.toFixed(0)} km
          </text>
          <text x="16" y={height / 2} fill="rgba(255,255,255,0.6)" fontSize="10" transform={`rotate(-90 16 ${height / 2})`}>
            {payload.yAxisLabel}
          </text>
          <text x={width / 2} y={height - 8} textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="10">
            {payload.xAxisLabel}
          </text>
        </svg>
      </div>
      <div className="flex items-center justify-between text-[11px] text-white/55">
        <span>Severidad {payload.severity_range[0].toFixed(1)} - {payload.severity_range[1].toFixed(1)}</span>
        <span>{payload.verticalExtent}</span>
      </div>
    </div>
  )
}
