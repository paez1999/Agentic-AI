"use client";

import type { PortStatus } from "@/lib/types";
import { Activity, AlertTriangle, ShieldCheck, Radio } from "lucide-react";
import { clsx } from "clsx";

interface MetricsBarProps {
  ports: PortStatus[];
}

export function MetricsBar({ ports }: MetricsBarProps) {
  const counts = {
    LOW: ports.filter((p) => p.risk_level === "LOW").length,
    MEDIUM: ports.filter((p) => p.risk_level === "MEDIUM").length,
    HIGH: ports.filter((p) => p.risk_level === "HIGH").length,
    CRITICAL: ports.filter((p) => p.risk_level === "CRITICAL").length,
  };
  const total = ports.length;
  const scanned = ports.filter((p) => p.scanned_at).length;
  const alerts = counts.HIGH + counts.CRITICAL;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <MetricCard
        icon={<Activity className="h-4 w-4" />}
        label="Total Nodes"
        value={total.toString().padStart(2, "0")}
        accent="cyan"
        sub={`${scanned}/${total} TELEMETRY OK`}
      />
      <MetricCard
        icon={<ShieldCheck className="h-4 w-4" />}
        label="Nominal"
        value={counts.LOW.toString().padStart(2, "0")}
        accent="emerald"
        sub="LOW RISK"
      />
      <MetricCard
        icon={<Radio className="h-4 w-4" />}
        label="Elevated"
        value={counts.MEDIUM.toString().padStart(2, "0")}
        accent="amber"
        sub="MEDIUM RISK"
      />
      <MetricCard
        icon={<AlertTriangle className="h-4 w-4" />}
        label="Alerts"
        value={alerts.toString().padStart(2, "0")}
        accent={alerts > 0 ? "red" : "slate"}
        sub={`${counts.HIGH} HIGH · ${counts.CRITICAL} CRIT`}
        pulse={alerts > 0}
      />
    </div>
  );
}

type Accent = "cyan" | "emerald" | "amber" | "red" | "slate";

const ACCENT: Record<Accent, { border: string; text: string; glow: string; barBg: string }> = {
  cyan: {
    border: "border-cyan-500/30",
    text: "text-cyan-300",
    glow: "before:bg-cyan-500/10",
    barBg: "bg-cyan-400",
  },
  emerald: {
    border: "border-emerald-500/30",
    text: "text-emerald-300",
    glow: "before:bg-emerald-500/10",
    barBg: "bg-emerald-400",
  },
  amber: {
    border: "border-amber-500/30",
    text: "text-amber-300",
    glow: "before:bg-amber-500/10",
    barBg: "bg-amber-400",
  },
  red: {
    border: "border-red-500/40",
    text: "text-red-300",
    glow: "before:bg-red-500/10",
    barBg: "bg-red-400",
  },
  slate: {
    border: "border-slate-700",
    text: "text-slate-300",
    glow: "before:bg-slate-700/10",
    barBg: "bg-slate-600",
  },
};

function MetricCard({
  icon,
  label,
  value,
  sub,
  accent,
  pulse = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  accent: Accent;
  pulse?: boolean;
}) {
  const a = ACCENT[accent];
  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-lg border bg-slate-900/60 backdrop-blur p-3",
        a.border,
        pulse && "critical-pulse"
      )}
    >
      {/* top accent bar */}
      <div className={clsx("absolute top-0 left-0 right-0 h-px", a.barBg, "opacity-60")} />
      <div className="flex items-center justify-between mb-2">
        <span className={clsx("flex items-center gap-1.5", a.text)}>
          {icon}
          <span className="font-mono text-[10px] uppercase tracking-wider">{label}</span>
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={clsx("font-mono font-bold text-2xl tabular-nums", a.text)}>
          {value}
        </span>
      </div>
      <p className="mt-0.5 font-mono text-[9px] uppercase tracking-wider text-slate-500">
        {sub}
      </p>
    </div>
  );
}
