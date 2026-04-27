"use client";

import type { RouteStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";
import { Wind, Thermometer, Droplets, Radar, ArrowRight, X } from "lucide-react";
import { clsx } from "clsx";

interface RouteCardProps {
  route: RouteStatus;
  onScan: (route_id: string) => void;
  onRemove: (route_id: string) => void;
}

const BORDER_BY_RISK: Record<string, string> = {
  LOW: "border-slate-800 hover:border-cyan-500/40",
  MEDIUM: "border-amber-500/30 hover:border-amber-500/60",
  HIGH: "border-orange-500/40 hover:border-orange-500/70",
  CRITICAL: "border-red-500/60 hover:border-red-500/80",
};

export function RouteCard({ route, onScan, onRemove }: RouteCardProps) {
  const lastScan = route.scanned_at ? new Date(route.scanned_at) : null;
  const ow = route.origin_weather;
  const dw = route.destination_weather;

  return (
    <div
      className={clsx(
        "group relative overflow-hidden rounded-lg border bg-slate-900/60 backdrop-blur transition-all hover-glow",
        BORDER_BY_RISK[route.risk_level] || BORDER_BY_RISK.LOW
      )}
    >
      {/* corner brackets */}
      <div className="absolute top-0 left-0 h-2 w-2 border-t border-l border-cyan-400/40" />
      <div className="absolute top-0 right-0 h-2 w-2 border-t border-r border-cyan-400/40" />
      <div className="absolute bottom-0 left-0 h-2 w-2 border-b border-l border-cyan-400/40" />
      <div className="absolute bottom-0 right-0 h-2 w-2 border-b border-r border-cyan-400/40" />

      <div className="p-4 flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 font-mono font-bold text-slate-100 text-base leading-tight flex-wrap">
              <span className="truncate">{route.origin.toUpperCase()}</span>
              <ArrowRight className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
              <span className="truncate">{route.destination.toUpperCase()}</span>
            </div>
            <p className="font-mono text-[10px] text-slate-600 mt-0.5 truncate">
              {route.route_id}
            </p>
          </div>
          <RiskBadge level={route.risk_level} />
        </div>

        {/* Summary */}
        <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 min-h-[2rem]">
          {route.summary}
        </p>

        {/* Planner rationale */}
        {route.planner_rationale && (
          <p className="text-[11px] italic text-slate-500 leading-relaxed -mt-1">
            {route.planner_rationale}
          </p>
        )}

        {/* Avoided chokepoints */}
        {route.avoid_used && route.avoid_used.length > 0 && (
          <div className="flex flex-wrap gap-1 -mt-1">
            {route.avoid_used.map((cp) => (
              <span
                key={cp}
                className="text-[10px] font-mono bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded px-1 py-0.5"
              >
                avoiding {cp}
              </span>
            ))}
          </div>
        )}

        {/* Weather grid */}
        {(ow || dw) ? (
          <div className="grid grid-cols-2 gap-2">
            <WeatherColumn label="ORIGIN" weather={ow} />
            <WeatherColumn label="DEST" weather={dw} />
          </div>
        ) : (
          <div className="rounded border border-dashed border-slate-800 bg-slate-950/60 p-2 text-center text-[11px] text-slate-600 font-mono">
            AWAITING TELEMETRY
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
          <div className="font-mono text-[10px] text-slate-600">
            {lastScan ? (
              <>
                <span className="text-slate-500">↻</span>{" "}
                {lastScan.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </>
            ) : (
              "NEVER SCANNED"
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onScan(route.route_id);
              }}
              className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/60 px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:bg-slate-700 hover:text-cyan-300 transition-colors"
              title="Scan now"
            >
              <Radar className="h-3 w-3" />
              Scan
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(route.route_id);
              }}
              className="inline-flex items-center gap-1 rounded border border-red-500/20 bg-red-500/10 px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-red-400 hover:bg-red-500/20 transition-colors"
              title="Remove route"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function WeatherColumn({
  label,
  weather,
}: {
  label: string;
  weather: import("@/lib/types").WeatherData | null;
}) {
  return (
    <div className="rounded border border-slate-800 bg-slate-950/60 p-2 flex flex-col gap-1.5">
      <span className="font-mono text-[9px] uppercase tracking-widest text-slate-500">
        {label}
      </span>
      {weather ? (
        <>
          <WeatherMetric
            icon={<Thermometer className="h-3 w-3" />}
            label="TEMP"
            value={`${weather.temperature_c.toFixed(1)}°`}
          />
          <WeatherMetric
            icon={<Droplets className="h-3 w-3" />}
            label="HUM"
            value={`${weather.humidity_pct}%`}
          />
          <WeatherMetric
            icon={<Wind className="h-3 w-3" />}
            label="WIND"
            value={`${weather.wind_speed_ms.toFixed(1)}m/s`}
          />
        </>
      ) : (
        <span className="font-mono text-[9px] text-slate-700 text-center py-1">
          NO DATA
        </span>
      )}
    </div>
  );
}

function WeatherMetric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-1">
      <div className="flex items-center gap-1 text-slate-500">
        {icon}
        <span className="font-mono text-[9px] uppercase tracking-wider">{label}</span>
      </div>
      <span className="font-mono text-[10px] font-semibold text-slate-100">{value}</span>
    </div>
  );
}
