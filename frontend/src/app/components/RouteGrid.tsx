"use client";

import { usePortStore } from "../hooks/usePortStore";
import { RouteCard } from "./RouteCard";
import { Route, Plus } from "lucide-react";

interface RouteGridProps {
  onAddRoute: () => void;
}

export function RouteGrid({ onAddRoute }: RouteGridProps) {
  const { routes, scanRoute, removeRoute } = usePortStore();

  // Sort: CRITICAL → HIGH → MEDIUM → LOW
  const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 } as const;
  const sorted = [...routes].sort((a, b) => order[a.risk_level] - order[b.risk_level]);

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Route className="h-3.5 w-3.5 text-cyan-400" />
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">
            Route Corridors
          </h2>
          <span className="font-mono text-xs text-slate-600">
            [{routes.length.toString().padStart(2, "0")}]
          </span>
        </div>
        <button
          onClick={onAddRoute}
          className="inline-flex items-center gap-1.5 rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-cyan-300 hover:bg-cyan-500/20 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Corridor
        </button>
      </div>

      {routes.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center">
          <Route className="h-6 w-6 text-slate-700 mx-auto mb-2" />
          <p className="text-sm text-slate-500 font-mono">NO ROUTES MONITORED</p>
          <p className="text-xs text-slate-600 mt-1">
            Add a corridor to begin tracking
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {sorted.map((route) => (
            <RouteCard
              key={route.route_id}
              route={route}
              onScan={(id) => { scanRoute(id).catch(console.error); }}
              onRemove={(id) => { removeRoute(id).catch(console.error); }}
            />
          ))}
        </div>
      )}
    </section>
  );
}
