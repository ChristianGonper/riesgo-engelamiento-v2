import React, { useState } from 'react';
import { Play, Pause } from 'lucide-react';
import { MapContainer, TileLayer, Polygon, Polyline, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Type definitions
type Point = [number, number];

function MapClickHandler({ onPointsSelected }: { onPointsSelected: (p1: Point, p2: Point) => void }) {
  const [points, setPoints] = useState<Point[]>([]);

  useMapEvents({
    click(e) {
      const newPoints = [...points, [e.latlng.lat, e.latlng.lng] as Point];
      if (newPoints.length > 2) {
        newPoints.shift();
      }
      setPoints(newPoints);
      if (newPoints.length === 2) {
        onPointsSelected(newPoints[0], newPoints[1]);
      }
    },
  });

  return (
    <>
      {points.map((p, i) => (
        <Polygon key={i} positions={[p]} />
      ))}
      {points.length === 2 && <Polyline positions={points} color="#00B0FF" weight={3} />}
    </>
  );
}

function App() {
  const [altitude, setAltitude] = useState(150);
  const [time, setTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [route, setRoute] = useState<{ p1: Point; p2: Point } | null>(null);

  const formatTime = (t: number) => {
    const hours = Math.floor(t) + 12;
    return `${hours.toString().padStart(2, '0')}:00Z`;
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-dark text-white font-ui selection:bg-info/30">
      {/* Base Map */}
      <div className="absolute inset-0 z-0">
        <MapContainer
          center={[40.4168, -3.7038]} // Madrid as default
          zoom={5}
          className="w-full h-full bg-[#080A10]"
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapClickHandler onPointsSelected={(p1, p2) => setRoute({ p1, p2 })} />
          
          {/* Mock Risk Overlay - Red polygon for severe risk */}
          <Polygon positions={[[42,-4], [43,-2], [41,0]]} pathOptions={{ color: '#FF1744', fillColor: '#FF1744', fillOpacity: 0.4, weight: 1 }} />
          {/* Yellow polygon for caution */}
          <Polygon positions={[[39,-6], [40,-5], [38,-3]]} pathOptions={{ color: '#FFD600', fillColor: '#FFD600', fillOpacity: 0.4, weight: 1 }} />
        </MapContainer>
      </div>

      {/* Header Panel */}
      <div className="absolute top-8 left-8 z-10 w-90 flex flex-col gap-4 frost-panel rounded-2xl p-6 shadow-2xl">
        <h1 className="text-2xl font-bold tracking-[0.2em]">AERO-FROST</h1>
        <h2 className="text-xs font-telemetry text-white/60 tracking-wider">ICING RISK TELEMETRY</h2>
      </div>

      {/* NACA Panel */}
      <div className="absolute top-8 right-8 z-10 w-72 h-44 flex flex-col gap-2 frost-panel rounded-2xl p-6 shadow-2xl">
        <div className="flex flex-row items-center justify-between w-full">
          <span className="text-xs font-bold">AERODYNAMIC THREAT</span>
          <div className="bg-severe/20 border border-severe rounded px-2 py-1 shadow-[0_0_10px_rgba(255,23,68,0.8)]">
            <span className="text-[10px] font-telemetry font-bold text-severe">SEVERE</span>
          </div>
        </div>
        <div className="flex-1 w-full flex items-center justify-center relative">
          <svg viewBox="0 0 200 60" className="w-full h-full drop-shadow-[0_0_15px_rgba(255,23,68,0.5)]">
            <path
              d="M0 30 Q 50 0 200 30 Q 50 60 0 30"
              fill="rgba(255,23,68,0.2)"
              stroke="#FF1744"
              strokeWidth="3"
            />
          </svg>
        </div>
      </div>

      {/* Cross Section Panel */}
      <div className="absolute bottom-8 right-8 z-10 w-[568px] h-[368px] flex flex-col frost-panel rounded-2xl p-6 shadow-2xl">
        <div className="flex flex-row w-full items-center justify-between mb-4">
          <span className="text-sm font-bold">ROUTE CROSS-SECTION</span>
          {route ? (
            <span className="text-xs font-telemetry text-white/60">
              FL{altitude} - {Math.round(Math.random()*100 + 200)}NM
            </span>
          ) : (
            <span className="text-xs font-telemetry text-white/60">CLICK 2 POINTS</span>
          )}
        </div>
        <div className="flex-1 w-full rounded-lg border border-white/10 bg-black/40 overflow-hidden relative">
          {/* Mock chart background gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-transparent via-safe/10 to-caution/40 opacity-50" />
          
          {/* Mock Chart SVG */}
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 520 260">
            {route ? (
               <path d="M0 260 L100 180 L250 120 L350 20 L520 100" stroke="#FFD600" strokeWidth="2" fill="none" />
            ) : (
               <text x="50%" y="50%" textAnchor="middle" fill="rgba(255,255,255,0.3)" className="font-telemetry text-sm">AWAITING ROUTE</text>
            )}
          </svg>
        </div>
      </div>

      {/* Controls Panel */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 w-[600px] flex flex-col gap-5 frost-panel rounded-3xl p-6 shadow-2xl">
        
        {/* Altitude Row */}
        <div className="flex flex-row items-center w-full gap-4">
          <span className="text-sm font-telemetry text-white/60">FL</span>
          <span className="text-sm font-telemetry font-bold text-info w-8">{altitude}</span>
          <div className="flex-1 relative h-6 flex items-center group cursor-pointer">
            <input
              type="range"
              min="0"
              max="400"
              step="10"
              value={altitude}
              onChange={(e) => setAltitude(parseInt(e.target.value))}
              className="absolute w-full h-full opacity-0 cursor-pointer z-20"
            />
            <div className="w-full h-1 bg-white/10 rounded-full relative z-0">
              <div 
                className="absolute top-0 left-0 h-full bg-info rounded-full" 
                style={{ width: `${(altitude / 400) * 100}%` }}
              />
              <div 
                className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-info rounded-full shadow-[0_0_10px_rgba(0,176,255,0.5)]"
                style={{ left: `calc(${(altitude / 400) * 100}% - 8px)` }}
              />
            </div>
          </div>
        </div>

        {/* Time Row */}
        <div className="flex flex-row items-center w-full gap-4">
          <button 
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause size={14} fill="white" /> : <Play size={14} fill="white" />}
          </button>
          <span className="text-sm font-telemetry font-bold w-14">{formatTime(time)}</span>
          <div className="flex-1 relative h-6 flex items-center group cursor-pointer">
             <input
              type="range"
              min="0"
              max="24"
              step="1"
              value={time}
              onChange={(e) => setTime(parseInt(e.target.value))}
              className="absolute w-full h-full opacity-0 cursor-pointer z-20"
            />
            <div className="w-full h-1 bg-white/10 rounded-full relative z-0">
              <div 
                className="absolute top-0 left-0 h-full bg-safe rounded-full" 
                style={{ width: `${(time / 24) * 100}%` }}
              />
              <div 
                className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-safe rounded-full shadow-[0_0_10px_rgba(0,230,118,0.5)]"
                style={{ left: `calc(${(time / 24) * 100}% - 8px)` }}
              />
            </div>
          </div>
        </div>

      </div>

    </div>
  )
}

export default App
