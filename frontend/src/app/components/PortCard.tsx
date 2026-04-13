"use client";

import type { PortStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";
import { Wind, Thermometer, Droplets, ChevronRight, Radar } from "lucide-react";
import { clsx } from "clsx";
import { usePortStore } from "../hooks/usePortStore";
import { EVENT_ICON } from "@/lib/eventIcons";

interface PortCardProps {
  port: PortStatus;
  onViewDetails: (port: PortStatus) => void;
  onScan: (city: string) => void;
}

const BORDER_BY_RISK: Record<string, string> = {
  LOW: "border-slate-800 hover:border-cyan-500/40",
  MEDIUM: "border-amber-500/30 hover:border-amber-500/60",
  HIGH: "border-orange-500/40 hover:border-orange-500/70",
  CRITICAL: "border-red-500/60 hover:border-red-500/80",
};

export function PortCard({ port, onViewDetails, onScan }: PortCardProps) {
  const w = port.weather;
  const lastScan = port.scanned_at ? new Date(port.scanned_at) : null;
  const { simulationsAffecting } = usePortStore();
  const activeSims = simulationsAffecting(port.city);

  const simBorder = activeSims.length > 0 ? "border-fuchsia-500/50" : "";

  return (
    <div
      className={clsx(
        "group relative overflow-hidden rounded-lg border bg-slate-900/60 backdrop-blur transition-all hover-glow",
        simBorder || BORDER_BY_RISK[port.risk_level] || BORDER_BY_RISK.LOW
      )}
    >
      {/* corner brackets */}
      <div className="absolute top-0 left-0 h-2 w-2 border-t border-l border-cyan-400/40" />
      <div className="absolute top-0 right-0 h-2 w-2 border-t border-r border-cyan-400/40" />
      <div className="absolute bottom-0 left-0 h-2 w-2 border-b border-l border-cyan-400/40" />
      <div className="absolute bottom-0 right-0 h-2 w-2 border-b border-r border-cyan-400/40" />

      {/* Simulation accent line */}
      {activeSims.length > 0 && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-fuchsia-400/70 to-transparent" />
      )}

      <div className="p-4 flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                NODE
              </span>
              <span className="font-mono text-[10px] text-slate-600">
                {port.city.substring(0, 3).toUpperCase()}-
                {(port.city.length * 7).toString().padStart(3, "0")}
              </span>
            </div>
            <h3 className="font-semibold text-slate-100 text-base leading-tight mt-0.5 truncate">
              {port.city}
            </h3>
            {w && (
              <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                {w.country}
              </p>
            )}
          </div>
          <RiskBadge level={port.risk_level} />
        </div>

        {/* Summary */}
        <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 min-h-[2rem]">
          {port.summary}
        </p>

        {/* Weather metrics */}
        {w && (
          <div className="grid grid-cols-3 gap-2 rounded border border-slate-800 bg-slate-950/60 p-2">
            <Metric
              icon={<Thermometer className="h-3 w-3" />}
              label="TEMP"
              value={`${w.temperature_c.toFixed(1)}°`}
            />
            <Metric
              icon={<Droplets className="h-3 w-3" />}
              label="HUM"
              value={`${w.humidity_pct}%`}
            />
            <Metric
              icon={<Wind className="h-3 w-3" />}
              label="WIND"
              value={`${w.wind_speed_ms.toFixed(1)}m/s`}
            />
          </div>
        )}
        {!w && (
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
                onScan(port.city);
              }}
              className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/60 px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:bg-slate-700 hover:text-cyan-300 transition-colors"
              title="Scan now"
            >
              <Radar className="h-3 w-3" />
              Scan
            </button>
            <button
              onClick={() => onViewDetails(port)}
              className="inline-flex items-center gap-1 rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-cyan-300 hover:bg-cyan-500/20 transition-colors"
            >
              Inspect
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="flex items-center gap-1 text-slate-500">
        {icon}
        <span className="font-mono text-[9px] uppercase tracking-wider">{label}</span>
      </div>
      <span className="font-mono text-xs font-semibold text-slate-100">{value}</span>
    </div>
  );
}
