"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, MapPin, Zap, Info } from "lucide-react";
import { api } from "@/lib/api";
import type { RouteType } from "@/lib/types";
import type { EventType, RiskLevel, RouteStatus, PortStatus } from "@/lib/types";
import {
  ALL_EVENT_TYPES,
  EVENT_ICON,
  EVENT_LABEL,
  EVENT_DEFAULT_SEVERITY,
} from "@/lib/eventIcons";

// City coords [lon, lat] — mirrors backend/geo_utils.py
const CITY_COORDS: Record<string, [number, number]> = {
  veracruz:        [-96.1342, 19.1738],
  houston:         [-95.3698, 29.7604],
  tampa:           [-82.4572, 27.9506],
  "mexico city":   [-99.1332, 19.4326],
  panama:          [-79.5197,  8.9936],
  miami:           [-80.1918, 25.7617],
  guatemala:       [-90.5069, 14.6349],
  "guatemala city":[-90.5069, 14.6349],
  "new orleans":   [-90.0715, 29.9511],
  "los angeles":   [-118.2437, 34.0522],
  "new york":      [-74.0060, 40.7128],
};

const SEVERITY_OPTIONS: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const SEVERITY_COLORS: Record<RiskLevel, string> = {
  LOW:      "border-emerald-500/50 bg-emerald-500/10 text-emerald-300",
  MEDIUM:   "border-yellow-500/50 bg-yellow-500/10 text-yellow-300",
  HIGH:     "border-orange-500/50 bg-orange-500/10 text-orange-300",
  CRITICAL: "border-red-500/50 bg-red-500/10 text-red-300",
};

import type { RouteType as _RouteType } from "@/lib/types"; // used below
const ROUTE_TYPE_STYLE: Record<string, { color: string; dashArray?: string; weight: number }> = {
  maritime:    { color: "#38bdf8", dashArray: "8 5",     weight: 2.5 },
  terrestrial: { color: "#f59e0b", dashArray: undefined,  weight: 2.5 },
  air:         { color: "#e2e8f0", dashArray: "4 6",     weight: 2.5 },
};

const LEAFLET_VERSION = "1.9.4";
const LEAFLET_CSS = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.css`;
const LEAFLET_JS  = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.js`;

/** Load Leaflet from CDN if not already present; resolves with window.L */
function loadLeaflet(): Promise<unknown> {
  return new Promise((resolve, reject) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((window as any).L) { resolve((window as any).L); return; }

    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }

    if (!document.getElementById("leaflet-js")) {
      const script = document.createElement("script");
      script.id = "leaflet-js";
      script.src = LEAFLET_JS;
      script.onload = () => resolve((window as any).L); // eslint-disable-line @typescript-eslint/no-explicit-any
      script.onerror = () => reject(new Error("Failed to load Leaflet from CDN"));
      document.head.appendChild(script);
    } else {
      // Script tag exists but may still be loading
      const wait = setInterval(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((window as any).L) { clearInterval(wait); resolve((window as any).L); }
      }, 50);
    }
  });
}

export interface MapDropDialogProps {
  ports: PortStatus[];
  routes: RouteStatus[];
  onClose: () => void;
  onCreated: () => void;
}

interface DroppedPin { lat: number; lon: number; }

export function MapDropDialog({ ports, routes, onClose, onCreated }: MapDropDialogProps) {
  const mapRef        = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const markerRef     = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const circleRef     = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const routeLayerRef = useRef<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const portLayerRef  = useRef<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any

  const [pin, setPin]                   = useState<DroppedPin | null>(null);
  const [eventType, setEventType]       = useState<EventType>("HURRICANE");
  const [severity, setSeverity]         = useState<RiskLevel>("CRITICAL");
  const [radiusKm, setRadiusKm]         = useState(300);
  const [description, setDescription]   = useState("");
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [leafletReady, setLeafletReady] = useState(false);
  const [routeGeometry, setRouteGeometry] = useState<Record<string, [number, number][]>>({});
  const [affectedPreview, setAffectedPreview] = useState<{
    cities: string[];
    routes: string[];
  } | null>(null);

  // Sync severity default with event type
  useEffect(() => {
    setSeverity(EVENT_DEFAULT_SEVERITY[eventType]);
  }, [eventType]);

  // ── Init map once ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current) return;
    let map: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    loadLeaflet().then((L: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
      if (!mapRef.current || leafletMapRef.current) return;
      map = L.map(mapRef.current, { center: [20, -88], zoom: 5 });
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "© OpenStreetMap © CARTO", maxZoom: 18,
      }).addTo(map);
      leafletMapRef.current = map;
      map.on("click", (e: any) => setPin({ lat: e.latlng.lat, lon: e.latlng.lng })); // eslint-disable-line @typescript-eslint/no-explicit-any
      setLeafletReady(true);
    });
    return () => { map?.remove(); leafletMapRef.current = null; setLeafletReady(false); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Fetch geometry for all routes ─────────────────────────────────────────
  useEffect(() => {
    if (routes.length === 0) return;
    Promise.all(
      routes.map((r) =>
        api.routes.geometry(r.route_id)
          .then((g) => ({ id: r.route_id, coords: g.coordinates }))
          .catch(() => ({ id: r.route_id, coords: [] as [number, number][] }))
      )
    ).then((results) => {
      const geo: Record<string, [number, number][]> = {};
      results.forEach(({ id, coords }) => { geo[id] = coords; });
      setRouteGeometry(geo);
    });
  }, [routes]);

  // ── Redraw routes whenever geometry or map readiness changes ──────────────
  useEffect(() => {
    if (!leafletReady) return;
    const L   = (window as any).L; // eslint-disable-line @typescript-eslint/no-explicit-any
    const map = leafletMapRef.current;
    if (!L || !map) return;
    routeLayerRef.current.forEach((l) => l.remove());
    routeLayerRef.current = [];
    routes.forEach((r) => {
      const geometry = routeGeometry[r.route_id];
      if (!geometry || geometry.length < 2) return;
      const latlngs  = geometry.map((pt) => [pt[1], pt[0]] as [number, number]);
      const style    = ROUTE_TYPE_STYLE[r.route_type as RouteType] ?? ROUTE_TYPE_STYLE.maritime;
      const typeIcon = r.route_type === "air" ? "✈️" : r.route_type === "terrestrial" ? "🚛" : "🚢";
      const line = L.polyline(latlngs, {
        color: style.color, weight: style.weight, opacity: 0.6,
        dashArray: style.dashArray,
      }).addTo(map).bindTooltip(`${typeIcon} ${r.origin} → ${r.destination}`, { sticky: true });
      routeLayerRef.current.push(line);
    });
  }, [routeGeometry, leafletReady]);

  // ── Redraw ports whenever ports list or map readiness changes ─────────────
  useEffect(() => {
    if (!leafletReady) return;
    const L   = (window as any).L; // eslint-disable-line @typescript-eslint/no-explicit-any
    const map = leafletMapRef.current;
    if (!L || !map) return;
    portLayerRef.current.forEach((l) => l.remove());
    portLayerRef.current = [];
    ports.forEach((p) => {
      const c = CITY_COORDS[p.city.toLowerCase()];
      const lat = c ? c[1] : p.lat;
      const lon = c ? c[0] : p.lon;
      if (lat == null || lon == null) return;
      // Shim so the rest of the block can still use `c` as [lon, lat]
      const c2: [number, number] = [lon, lat];
      const icon = L.divIcon({
        className: "",
        html: `<div style="width:10px;height:10px;background:#38bdf8;border:2px solid #0ea5e9;border-radius:50%;box-shadow:0 0 6px #38bdf8"></div>`,
        iconSize: [10, 10], iconAnchor: [5, 5],
      });
      const m = L.marker([c2[1], c2[0]], { icon }).addTo(map).bindTooltip(p.city);
      portLayerRef.current.push(m);
    });
  }, [ports, leafletReady]);

  // Update pin marker + radius circle whenever pin/radius/eventType changes
  useEffect(() => {
    if (!leafletReady) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const L = (window as any).L;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const map = leafletMapRef.current as any;
    if (!L || !map) return;

    // Remove previous pin & circle
    if (markerRef.current) { markerRef.current.remove(); markerRef.current = null; }
    if (circleRef.current) { circleRef.current.remove(); circleRef.current = null; }

    if (!pin) return;

    const icon = L.divIcon({
      className: "",
      html: `<div style="font-size:28px;line-height:1;filter:drop-shadow(0 0 6px rgba(255,100,0,0.9));transform:translate(-50%,-100%)">${EVENT_ICON[eventType]}</div>`,
      iconSize: [32, 32], iconAnchor: [16, 32],
    });
    const marker = L.marker([pin.lat, pin.lon], { icon }).addTo(map);
    marker.bindPopup(`<strong>${EVENT_LABEL[eventType]}</strong><br>${pin.lat.toFixed(3)}°, ${pin.lon.toFixed(3)}°`);
    markerRef.current = marker;

    const circle = L.circle([pin.lat, pin.lon], {
      radius: radiusKm * 1000,
      color: "#f97316", weight: 2,
      fillColor: "#f97316", fillOpacity: 0.12, dashArray: "6 4",
    }).addTo(map);
    circleRef.current = circle;

    // Affected preview (client-side geometry check)
    const affectedCities = ports
      .filter((p) => {
        const c = CITY_COORDS[p.city.toLowerCase()];
        const lat = c ? c[1] : p.lat;
        const lon = c ? c[0] : p.lon;
        if (lat == null || lon == null) return false;
        return haversineKm(pin.lat, pin.lon, lat, lon) <= radiusKm;
      })
      .map((p) => p.city);

    const affectedRoutes = routes
      .filter((r) => {
        const geo = routeGeometry[r.route_id];
        if (geo && geo.length > 0) {
          // Use actual fetched route geometry — works for any city pair
          return geo.some(([lon, lat]) => haversineKm(pin.lat, pin.lon, lat, lon) <= radiusKm);
        }
        // Fallback: straight-line interpolation via CITY_COORDS
        return routeIntersects(r.origin, r.destination, pin.lat, pin.lon, radiusKm);
      })
      .map((r) => `${r.origin} → ${r.destination}`);

    setAffectedPreview({ cities: affectedCities, routes: affectedRoutes });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pin, radiusKm, eventType, leafletReady]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pin) return;
    setLoading(true);
    setError(null);
    try {
      await api.simulations.createFromCoordinates({
        lat: pin.lat, lon: pin.lon, radius_km: radiusKm,
        event_type: eventType, severity,
        description: description.trim() || undefined,
      });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create simulation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-stretch bg-slate-950/90 backdrop-blur-sm">
      {/* Map */}
      <div className="relative flex-1">
        <div ref={mapRef} className="h-full w-full" style={{ background: "#0f172a" }} />

        {!pin && (
          <div className="pointer-events-none absolute left-1/2 top-6 -translate-x-1/2 rounded border border-fuchsia-500/40 bg-slate-900/90 px-4 py-2 text-[11px] uppercase tracking-widest text-fuchsia-300">
            <MapPin className="mr-1.5 inline h-3 w-3" />
            Click anywhere on the map to drop the event
          </div>
        )}

        {pin && (
          <div className="pointer-events-none absolute bottom-4 left-4 rounded border border-slate-700 bg-slate-900/90 px-3 py-1.5 font-mono text-[10px] text-slate-400">
            {pin.lat.toFixed(4)}°, {pin.lon.toFixed(4)}°
          </div>
        )}

        <button
          onClick={onClose}
          style={{ zIndex: 1000 }}
          className="absolute left-4 top-4 flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-[11px] text-slate-300 transition-colors hover:text-slate-100"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Go Back
        </button>
      </div>

      {/* Control panel */}
      <div className="flex w-80 flex-col gap-4 overflow-y-auto border-l border-slate-800 bg-slate-950 p-5">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-fuchsia-400" />
          <span className="text-[11px] font-semibold uppercase tracking-widest text-fuchsia-300">
            Drop Simulation
          </span>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Event type */}
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-widest text-slate-500">Event Type</p>
            <div className="grid grid-cols-3 gap-1.5">
              {ALL_EVENT_TYPES.map((et) => (
                <button
                  key={et} type="button" onClick={() => setEventType(et)}
                  className={`flex flex-col items-center gap-0.5 rounded border p-1.5 text-[9px] uppercase tracking-wider transition-colors ${
                    eventType === et
                      ? "border-fuchsia-500/60 bg-fuchsia-500/20 text-fuchsia-200"
                      : "border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  <span className="text-base leading-none">{EVENT_ICON[et]}</span>
                  <span className="leading-none">{EVENT_LABEL[et].split(" ")[0]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Radius */}
          <div>
            <p className="mb-1.5 text-[10px] uppercase tracking-widest text-slate-500">
              Impact Radius — <span className="text-orange-400">{radiusKm} km</span>
            </p>
            <input
              type="range" min={50} max={800} step={25} value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="w-full accent-orange-500"
            />
            <div className="mt-0.5 flex justify-between text-[9px] text-slate-600">
              <span>50 km</span><span>800 km</span>
            </div>
          </div>

          {/* Severity */}
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-widest text-slate-500">Severity</p>
            <div className="grid grid-cols-2 gap-1.5">
              {SEVERITY_OPTIONS.map((s) => (
                <button
                  key={s} type="button" onClick={() => setSeverity(s)}
                  className={`rounded border px-2 py-1 text-[10px] uppercase tracking-wider transition-colors ${
                    severity === s ? SEVERITY_COLORS[s] : "border-slate-700 bg-slate-900 text-slate-500 hover:border-slate-600"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <p className="mb-1.5 text-[10px] uppercase tracking-widest text-slate-500">
              Description <span className="text-slate-600">(optional)</span>
            </p>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={`${EVENT_ICON[eventType]} ${EVENT_LABEL[eventType]} scenario…`}
              rows={3}
              className="w-full resize-none rounded border border-slate-700 bg-slate-900 px-3 py-2 text-[11px] text-slate-200 placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:outline-none"
            />
          </div>

          {/* Impact preview */}
          {pin && affectedPreview && (
            <div className="rounded border border-slate-800 bg-slate-900/60 p-3 text-[10px]">
              <div className="mb-1.5 flex items-center gap-1.5">
                <Info className="h-3 w-3 text-cyan-400" />
                <span className="uppercase tracking-wider text-cyan-400">Impact Preview</span>
              </div>
              {affectedPreview.cities.length > 0 ? (
                <p className="text-slate-300"><span className="text-slate-500">Ports: </span>{affectedPreview.cities.join(", ")}</p>
              ) : (
                <p className="text-slate-600">No monitored ports in radius</p>
              )}
              {affectedPreview.routes.length > 0 ? (
                <p className="mt-1 text-slate-300"><span className="text-slate-500">Routes: </span>{affectedPreview.routes.join(" · ")}</p>
              ) : (
                <p className="mt-1 text-slate-600">No routes pass through radius</p>
              )}
            </div>
          )}

          {!pin && (
            <p className="rounded border border-slate-800 bg-slate-900/60 px-3 py-2 text-center text-[10px] text-slate-500">
              Click the map to drop the event pin
            </p>
          )}

          {error && <p className="text-[10px] text-red-400">{error}</p>}

          <button
            type="submit" disabled={loading || !pin}
            className="inline-flex items-center justify-center gap-1.5 rounded border border-fuchsia-500/40 bg-fuchsia-500/15 px-4 py-2 text-[11px] uppercase tracking-[0.15em] text-fuchsia-200 transition-colors hover:bg-fuchsia-500/25 disabled:opacity-40"
          >
            <Zap className="h-3 w-3" />
            {loading ? "Injecting…" : "Inject Event"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ── Geo helpers (mirror backend/geo_utils.py) ─────────────────────────────────

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const r = (d: number) => (d * Math.PI) / 180;
  const a =
    Math.sin(r(lat2 - lat1) / 2) ** 2 +
    Math.cos(r(lat1)) * Math.cos(r(lat2)) * Math.sin(r(lon2 - lon1) / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function routeIntersects(
  origin: string, destination: string,
  evLat: number, evLon: number, radiusKm: number, steps = 30
): boolean {
  const o = CITY_COORDS[origin.toLowerCase()];
  const d = CITY_COORDS[destination.toLowerCase()];
  if (!o || !d) return false;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    if (haversineKm(evLat, evLon, o[1] + t * (d[1] - o[1]), o[0] + t * (d[0] - o[0])) <= radiusKm) return true;
  }
  return false;
}
