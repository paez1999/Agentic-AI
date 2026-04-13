"use client";

import type { PortStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";
import { AlertTriangle, Shield, ChevronRight } from "lucide-react";
import { clsx } from "clsx";

interface AlertPanelProps {
  ports: PortStatus[];
  onViewDetails: (port: PortStatus) => void;
}

export function AlertPanel({ ports, onViewDetails }: AlertPanelProps) {
  const alerts = ports
    .filter((p) => p.risk_level === "HIGH" || p.risk_level === "CRITICAL")
    .sort((a, b) => {
      if (a.risk_level === "CRITICAL" && b.risk_level !== "CRITICAL") return -1;
      if (b.risk_level === "CRITICAL" && a.risk_level !== "CRITICAL") return 1;
      return (b.scanned_at ?? "").localeCompare(a.scanned_at ?? "");
    });

  if (alerts.length === 0) {
    return (
      <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.03] p-4 flex items-center gap-3">
        <div className="relative">
          <Shield className="h-5 w-5 text-emerald-400" />
          <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400 live-dot" />
        </div>
        <div className="flex-1">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400">
            System Normal
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            All monitored nodes within safe thresholds
          </p>
        </div>
        <span className="font-mono text-[10px] text-slate-600 uppercase tracking-wider">
          STATUS: NOMINAL
        </span>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-lg border border-red-500/40 bg-red-950/20">
      <div className="absolute inset-0 scan-sweep pointer-events-none" />
      <div className="relative px-4 py-3 border-b border-red-500/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-red-400 critical-pulse rounded-full" />
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-red-300">
            Active Threat Feed
          </h2>
          <span className="font-mono text-xs text-red-400/80">
            [{alerts.length.toString().padStart(2, "0")}]
          </span>
        </div>
        <span className="font-mono text-[10px] text-red-400/70 uppercase tracking-wider">
          Priority: ELEVATED
        </span>
      </div>
      <ul className="divide-y divide-red-500/10">
        {alerts.map((port, idx) => (
          <li
            key={port.city}
            className={clsx(
              "flex items-center justify-between gap-3 px-4 py-2.5 hover:bg-red-500/5 transition-colors cursor-pointer group",
              port.risk_level === "CRITICAL" && "bg-red-500/[0.04]"
            )}
            onClick={() => onViewDetails(port)}
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="font-mono text-[10px] text-slate-600 w-6">
                {(idx + 1).toString().padStart(2, "0")}
              </span>
              <RiskBadge level={port.risk_level} compact />
              <span className="font-semibold text-slate-100 text-sm">{port.city}</span>
              <span className="text-xs text-slate-500 truncate hidden sm:inline">
                — {port.summary}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="font-mono text-[10px] text-slate-500 hidden md:inline">
                {port.scanned_at
                  ? new Date(port.scanned_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : ""}
              </span>
              <ChevronRight className="h-4 w-4 text-red-400/60 group-hover:text-red-300 transition-colors" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
