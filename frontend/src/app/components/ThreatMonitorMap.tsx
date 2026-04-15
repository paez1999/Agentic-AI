"use client";

import { useEffect, useRef, useState } from "react";
import { X, Globe, AlertTriangle, Clock, MapPin, Anchor, Route, ArrowLeft } from "lucide-react";
import type { SimulationEvent, PortStatus, RouteStatus, RiskLevel } from "@/lib/types";
import { EVENT_ICON, EVENT_LABEL } from "@/lib/eventIcons";
import { api } from "@/lib/api";

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

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW:      "#22c55e",
  MEDIUM:   "#eab308",
  HIGH:     "#f97316",
  CRITICAL: "#ef4444",
};

const ROUTE_TYPE_STYLE: Record<string, { dashArray?: string; weight: number }> = {
  maritime:    { dashArray: "8 5",    weight: 2.5 },
  terrestrial: { dashArray: undefined, weight: 2.5 },
  air:         { dashArray: "4 6",    weight: 2.5 },
};

const SEVERITY_BADGE: Record<string, string> = {
  LOW:      "border-emerald-500/50 bg-emerald-500/15 text-emerald-300",
  MEDIUM:   "border-yellow-500/50  bg-yellow-500/15  text-yellow-300",
  HIGH:     "border-orange-500/50  bg-orange-500/15  text-orange-300",
  CRITICAL: "border-red-500/50     bg-red-500/15     text-red-300",
};

const LEAFLET_VERSION = "1.9.4";

function loadLeaflet(): Promise<any> { // eslint-disable-line @typescript-eslint/no-explicit-any
  return new Promise((resolve, reject) => {
    const w = window as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (w.L) { resolve(w.L); return; }
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css"; link.rel = "stylesheet";
      link.href = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.css`;
      document.head.appendChild(link);
    }
    if (!document.getElementById("leaflet-js")) {
      const s = document.createElement("script");
      s.id = "leaflet-js";
      s.src = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/leaflet.js`;
      s.onload  = () => resolve(w.L);
      s.onerror = () => reject(new Error("Failed to load Leaflet"));
      document.head.appendChild(s);
    } else {
      const t = setInterval(() => { if (w.L) { clearInterval(t); resolve(w.L); } }, 50);
    }
  });
}

export interface ThreatMonitorMapProps {
  simulations: SimulationEvent[];
  ports: PortStatus[];
  routes: RouteStatus[];
  onClose: () => void;
}

export function ThreatMonitorMap({ simulations, ports, routes, onClose }: ThreatMonitorMapProps) {
  const mapRef        = useRef<HTMLDivElement>(null);
  const mapInst       = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const routeLayerRef = useRef<any[]>([]);  // eslint-disable-line @typescript-eslint/no-explicit-any
  const portLayerRef  = useRef<any[]>([]);  // eslint-disable-line @typescript-eslint/no-explicit-any
  const simLayerRef   = useRef<any[]>([]);  // eslint-disable-line @typescript-eslint/no-explicit-any

  const [leafletReady, setLeafletReady] = useState(false);
  const [selected, setSelected]         = useState<SimulationEvent | null>(null);
  // route_id → [lon, lat][] from backend geometry endpoint
  const [routeGeometry, setRouteGeometry] = useState<Record<string, [number, number][]>>({});

  // ── Init map once ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current) return;
    let map: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    loadLeaflet().then((L: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
      if (!mapRef.current || mapInst.current) return;
      map = L.map(mapRef.current, { center: [20, -88], zoom: 4 });
      mapInst.current = map;
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "© OpenStreetMap © CARTO", maxZoom: 18,
      }).addTo(map);
      setLeafletReady(true);
    });
    return () => { map?.remove(); mapInst.current = null; setLeafletReady(false); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Fetch geometry for all routes whenever the route list changes ─────────
  useEffect(() => {
    if (routes.length === 0) return;
    Promise.all(
      routes.map((r) =>
        api.routes.geometry(r.route_id)
          .then((g) => ({ id: r.route_id, coords: g.coordinates }))
          .catch(() => ({ id: r.route_id, coords: [] as [number, number][] }))
      )
    ).then((results) => {
      const map: Record<string, [number, number][]> = {};
      results.forEach(({ id, coords }) => { map[id] = coords; });
      setRouteGeometry(map);
    });
  }, [routes]);

  // ── Redraw routes whenever geometry or map readiness changes ───────────────
  useEffect(() => {
    if (!leafletReady) return;
    const L   = (window as any).L; // eslint-disable-line @typescript-eslint/no-explicit-any
    const map = mapInst.current as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (!L || !map) return;

    routeLayerRef.current.forEach((l) => l.remove());
    routeLayerRef.current = [];

    routes.forEach((r) => {
      const geometry = routeGeometry[r.route_id];
      if (!geometry || geometry.length < 2) return;
      // geometry is [lon, lat][] — Leaflet needs [lat, lon][]
      const latlngs = geometry.map((pt) => [pt[1], pt[0]] as [number, number]);
      const style    = ROUTE_TYPE_STYLE[r.route_type] ?? ROUTE_TYPE_STYLE.maritime;
      const color    = RISK_COLORS[r.risk_level] ?? "#64748b";
      const typeIcon = r.route_type === "air" ? "✈️" : r.route_type === "terrestrial" ? "🚛" : "🚢";
      const line = L.polyline(latlngs, {
        color,
        dashArray: style.dashArray,
        weight: style.weight,
        opacity: 0.85,
      }).addTo(map).bindTooltip(
        `${typeIcon} <strong>${r.origin} → ${r.destination}</strong><br>Mode: ${r.route_type} · Risk: ${r.risk_level}`,
        { sticky: true }
      );
      routeLayerRef.current.push(line);
    });
  }, [routeGeometry, leafletReady]);

  // ── Redraw ports whenever ports or map changes ─────────────────────────────
  useEffect(() => {
    if (!leafletReady) return;
    const L   = (window as any).L; // eslint-disable-line @typescript-eslint/no-explicit-any
    const map = mapInst.current as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (!L || !map) return;

    portLayerRef.current.forEach((l) => l.remove());
    portLayerRef.current = [];

    ports.forEach((p) => {
      const c = CITY_COORDS[p.city.toLowerCase()];
      if (!c) return;
      const color = RISK_COLORS[p.risk_level] ?? "#64748b";
      const icon  = L.divIcon({
        className: "",
        html: `<div style="width:14px;height:14px;background:${color};border:2px solid rgba(255,255,255,0.25);border-radius:50%;box-shadow:0 0 8px ${color}"></div>`,
        iconSize: [14, 14], iconAnchor: [7, 7],
      });
      const m = L.marker([c[1], c[0]], { icon }).addTo(map)
        .bindTooltip(`<strong>${p.city}</strong><br>Risk: ${p.risk_level}`, { sticky: true });
      portLayerRef.current.push(m);
    });
  }, [ports, leafletReady]);

  // ── Redraw simulation events whenever sims or map changes ──────────────────
  useEffect(() => {
    if (!leafletReady) return;
    const L   = (window as any).L; // eslint-disable-line @typescript-eslint/no-explicit-any
    const map = mapInst.current as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (!L || !map) return;

    simLayerRef.current.forEach((l) => l.remove());
    simLayerRef.current = [];

    simulations.forEach((sim) => {
      // Polygon risk zone
      if (sim.polygon?.length) {
        const poly = L.polygon(sim.polygon.map((pt: number[]) => [pt[1], pt[0]]), {
          color: "#f97316", weight: 1.5, fillColor: "#f97316", fillOpacity: 0.15,
        }).addTo(map);
        simLayerRef.current.push(poly);
      }

      // Radius circle (coordinate-drop sims)
      if (sim.coordinates && sim.radius_km) {
        const circle = L.circle([sim.coordinates[0], sim.coordinates[1]], {
          radius: sim.radius_km * 1000,
          color: "#f97316", weight: 1.5, dashArray: "5 4",
          fillColor: "#f97316", fillOpacity: 0.1,
        }).addTo(map);
        simLayerRef.current.push(circle);
      }

      // Marker positions
      const positions: Array<[number, number]> = [];
      if (sim.coordinates) {
        positions.push([sim.coordinates[0], sim.coordinates[1]]);
      } else {
        sim.affected_cities.forEach((city) => {
          const c = CITY_COORDS[city.toLowerCase()];
          if (c) positions.push([c[1], c[0]]);
        });
      }

      positions.forEach(([lat, lon]) => {
        const icon = L.divIcon({
          className: "",
          html: `<div style="font-size:26px;line-height:1;filter:drop-shadow(0 0 8px rgba(249,115,22,0.9));transform:translate(-50%,-100%)">${EVENT_ICON[sim.event_type]}</div>`,
          iconSize: [30, 30], iconAnchor: [15, 30],
        });
        const marker = L.marker([lat, lon], { icon })
          .addTo(map)
          .on("click", () => setSelected((prev) => prev?.sim_id === sim.sim_id ? null : sim))
          .bindTooltip(
            `${EVENT_ICON[sim.event_type]} <strong>${EVENT_LABEL[sim.event_type]}</strong><br>Severity: ${sim.severity}<br><em>Click for details</em>`,
            { sticky: true }
          );
        simLayerRef.current.push(marker);
      });
    });
  }, [simulations, leafletReady]);

  const activeCount   = simulations.length;
  const criticalCount = simulations.filter((s) => s.severity === "CRITICAL").length;

  return (
    <div className="fixed inset-0 z-50 flex items-stretch bg-slate-950/90 backdrop-blur-sm">
      {/* Map */}
      <div className="relative flex-1">
        <div ref={mapRef} className="h-full w-full" style={{ background: "#0f172a" }} />

        {/* Status bar */}
        <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900/90 px-3 py-1.5">
            <Globe className="h-3 w-3 text-cyan-400" />
            <span className="text-[10px] uppercase tracking-widest text-cyan-300">Threat Monitor</span>
          </div>
          {activeCount > 0 && (
            <div className="rounded border border-orange-500/40 bg-orange-500/10 px-2.5 py-1 text-[10px] text-orange-300">
              {activeCount} active
            </div>
          )}
          {criticalCount > 0 && (
            <div className="rounded border border-red-500/40 bg-red-500/10 px-2.5 py-1 text-[10px] text-red-300">
              {criticalCount} critical
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="pointer-events-none absolute bottom-6 left-4 rounded border border-slate-700 bg-slate-900/90 p-3 text-[9px] uppercase tracking-wider text-slate-400">
          <p className="mb-1.5 text-slate-500">Risk Level</p>
          {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as RiskLevel[]).map((lvl) => (
            <div key={lvl} className="mb-0.5 flex items-center gap-2">
              <span style={{ background: RISK_COLORS[lvl] }} className="inline-block h-2 w-4 rounded-sm" />
              {lvl}
            </div>
          ))}
          <p className="mb-1.5 mt-2 text-slate-500">Route Mode</p>
          {[
            { label: "Maritime",    icon: "🚢", dash: "dashed" },
            { label: "Terrestrial", icon: "🚛", dash: "solid"  },
            { label: "Air",         icon: "✈️", dash: "dotted" },
          ].map(({ label, icon, dash }) => (
            <div key={label} className="mb-0.5 flex items-center gap-2">
              <span className="text-[11px]">{icon}</span>
              <span>{label}</span>
              <span className="text-slate-600">({dash})</span>
            </div>
          ))}
        </div>

        {activeCount === 0 && (
          <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
            <Globe className="mx-auto mb-2 h-8 w-8 text-slate-700" />
            <p className="text-[11px] uppercase tracking-widest text-slate-600">No active threats</p>
          </div>
        )}

        {/* Go Back — explicit z-index beats Leaflet tile layers (z-index ~400) */}
        <button
          onClick={onClose}
          style={{ zIndex: 1000, position: "absolute", top: 16, right: 16 }}
          className="flex items-center gap-2 rounded border border-slate-600 bg-slate-900/95 px-3 py-2 text-[11px] uppercase tracking-widest text-slate-300 shadow-lg transition-colors hover:bg-slate-800 hover:text-white"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Go Back
        </button>
      </div>

      {/* Side panel */}
      <div className="flex w-72 flex-col border-l border-slate-800 bg-slate-950">
        <div className="border-b border-slate-800 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-400" />
            <span className="text-[11px] font-semibold uppercase tracking-widest text-orange-300">Active Threats</span>
            {activeCount > 0 && (
              <span className="ml-auto rounded-full border border-orange-500/30 bg-orange-500/10 px-2 py-0.5 text-[10px] text-orange-300">
                {activeCount}
              </span>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeCount === 0 ? (
            <div className="p-6 text-center">
              <p className="text-[10px] uppercase tracking-wider text-slate-600">No active threats</p>
            </div>
          ) : (
            simulations.map((sim) => (
              <button
                key={sim.sim_id}
                onClick={() => setSelected(selected?.sim_id === sim.sim_id ? null : sim)}
                className={`w-full border-b border-slate-800/60 p-3 text-left transition-colors hover:bg-slate-900/60 ${
                  selected?.sim_id === sim.sim_id ? "bg-slate-900/80" : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{EVENT_ICON[sim.event_type]}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[11px] font-medium text-slate-200">{EVENT_LABEL[sim.event_type]}</p>
                    <p className="text-[9px] uppercase tracking-wider text-slate-500">
                      {sim.affected_cities.length > 0
                        ? sim.affected_cities.join(", ")
                        : sim.coordinates
                        ? `${sim.coordinates[0].toFixed(1)}°, ${sim.coordinates[1].toFixed(1)}°`
                        : "Open ocean"}
                    </p>
                  </div>
                  <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[9px] uppercase ${SEVERITY_BADGE[sim.severity]}`}>
                    {sim.severity}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Detail card */}
        {selected && (
          <div className="border-t border-slate-700 bg-slate-900/60 p-4">
            <div className="mb-3 flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{EVENT_ICON[selected.event_type]}</span>
                <div>
                  <p className="text-[12px] font-semibold text-slate-100">{EVENT_LABEL[selected.event_type]}</p>
                  <span className={`rounded border px-1.5 py-0.5 text-[9px] uppercase ${SEVERITY_BADGE[selected.severity]}`}>
                    {selected.severity}
                  </span>
                </div>
              </div>
              <button onClick={() => setSelected(null)} className="text-slate-600 hover:text-slate-400">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <p className="mb-3 text-[11px] leading-relaxed text-slate-400">{selected.description}</p>

            {selected.coordinates && (
              <div className="mb-2 flex items-center gap-1.5 text-[10px] text-slate-500">
                <MapPin className="h-3 w-3 text-orange-400" />
                <span>
                  {selected.coordinates[0].toFixed(3)}°, {selected.coordinates[1].toFixed(3)}°
                  {selected.radius_km && ` · ${selected.radius_km} km radius`}
                </span>
              </div>
            )}

            {selected.affected_cities.length > 0 && (
              <div className="mb-2 flex items-start gap-1.5 text-[10px] text-slate-500">
                <Anchor className="mt-0.5 h-3 w-3 shrink-0 text-cyan-400" />
                <span><span className="text-slate-400">Ports: </span>{selected.affected_cities.join(", ")}</span>
              </div>
            )}

            {(() => {
              const affected = routes.filter(
                (r) => selected.affected_cities.includes(r.origin) || selected.affected_cities.includes(r.destination)
              );
              return affected.length > 0 ? (
                <div className="mb-2 flex items-start gap-1.5 text-[10px] text-slate-500">
                  <Route className="mt-0.5 h-3 w-3 shrink-0 text-green-400" />
                  <span>
                    <span className="text-slate-400">Routes: </span>
                    {affected.map((r) => `${r.origin} → ${r.destination}`).join(", ")}
                  </span>
                </div>
              ) : null;
            })()}

            <div className="mt-2 flex items-center gap-1.5 text-[9px] text-slate-600">
              <Clock className="h-3 w-3" />
              {new Date(selected.created_at).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
