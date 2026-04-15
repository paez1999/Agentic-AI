"use client";

import { useState } from "react";
import { X, Plus, Navigation } from "lucide-react";
import { usePortStore } from "../hooks/usePortStore";
import type { RouteType } from "@/lib/types";

interface AddRouteDialogProps {
  onClose: () => void;
}

const ROUTE_TYPES: { type: RouteType; label: string; icon: string; desc: string }[] = [
  { type: "maritime",    label: "Maritime",     icon: "🚢", desc: "Sea lanes & shipping routes" },
  { type: "terrestrial", label: "Terrestrial",  icon: "🚛", desc: "Road & rail corridors" },
  { type: "air",         label: "Air",          icon: "✈️", desc: "Airfreight & flight paths" },
];

export function AddRouteDialog({ onClose }: AddRouteDialogProps) {
  const { addRoute } = usePortStore();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [routeType, setRouteType] = useState<RouteType>("maritime");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const o = origin.trim();
    const d = destination.trim();
    if (!o || !d) return;
    setLoading(true);
    setError("");
    try {
      await addRoute(o, d, routeType);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-sm rounded-lg border border-cyan-500/30 bg-slate-900 shadow-[0_0_40px_-10px_rgba(34,211,238,0.3)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent" />

        {/* Header */}
        <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Navigation className="h-4 w-4 text-cyan-400" />
            <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-200">
              Register Route Corridor
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4">
          {/* Transport mode */}
          <div>
            <label className="mb-2 block font-mono text-[10px] uppercase tracking-wider text-slate-500">
              Transport Mode
            </label>
            <div className="grid grid-cols-3 gap-2">
              {ROUTE_TYPES.map(({ type, label, icon, desc }) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setRouteType(type)}
                  title={desc}
                  className={`flex flex-col items-center gap-1 rounded border py-2.5 text-[10px] uppercase tracking-wider transition-colors ${
                    routeType === type
                      ? "border-cyan-500/60 bg-cyan-500/15 text-cyan-200"
                      : "border-slate-700 bg-slate-950 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  <span className="text-xl leading-none">{icon}</span>
                  <span>{label}</span>
                </button>
              ))}
            </div>
            <p className="mt-1.5 text-[9px] text-slate-600">
              {ROUTE_TYPES.find((t) => t.type === routeType)?.desc}
            </p>
          </div>

          {/* Origin */}
          <div className="flex flex-col gap-1.5">
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
              Origin
            </label>
            <input
              autoFocus
              type="text"
              placeholder="e.g. Rotterdam"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          {/* Destination */}
          <div className="flex flex-col gap-1.5">
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
              Destination
            </label>
            <input
              type="text"
              placeholder="e.g. Singapore"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          {error && (
            <p className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300 font-mono">
              ERR: {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !origin.trim() || !destination.trim()}
            className="inline-flex items-center justify-center gap-2 rounded border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 font-mono text-xs uppercase tracking-[0.15em] text-cyan-300 hover:bg-cyan-500/20 disabled:opacity-40 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            {loading ? "Registering…" : "Register & Scan"}
          </button>
        </form>
      </div>
    </div>
  );
}
