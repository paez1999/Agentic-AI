import type { RiskLevel } from "@/lib/types";
import { clsx } from "clsx";

const STYLES: Record<RiskLevel, { cls: string; dot: string }> = {
  LOW: {
    cls: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    dot: "bg-emerald-400",
  },
  MEDIUM: {
    cls: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    dot: "bg-amber-400",
  },
  HIGH: {
    cls: "bg-orange-500/10 text-orange-300 border-orange-500/40",
    dot: "bg-orange-400",
  },
  CRITICAL: {
    cls: "bg-red-500/15 text-red-300 border-red-500/50 critical-pulse",
    dot: "bg-red-400",
  },
};

export function RiskBadge({ level, compact = false }: { level: RiskLevel; compact?: boolean }) {
  const style = STYLES[level];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded border font-mono font-semibold uppercase tracking-wider",
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]",
        style.cls
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", style.dot)} />
      {level}
    </span>
  );
}
