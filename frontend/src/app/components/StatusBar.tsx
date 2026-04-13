"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";

interface StatusBarProps {
  connected: boolean;
  autoScanEnabled: boolean;
  autoScanInterval: number;
  nodeCount: number;
}

export function StatusBar({
  connected,
  autoScanEnabled,
  autoScanInterval,
  nodeCount,
}: StatusBarProps) {
  const [clock, setClock] = useState<string>("--:--:--");

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setClock(
        now.toLocaleTimeString([], {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }) +
          " · UTC" +
          (now.getTimezoneOffset() > 0 ? "-" : "+") +
          String(Math.abs(now.getTimezoneOffset() / 60)).padStart(2, "0")
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 py-1.5 flex items-center justify-between gap-4 font-mono text-[10px] uppercase tracking-wider">
        <div className="flex items-center gap-4 text-slate-500">
          <div className="flex items-center gap-1.5">
            <span
              className={clsx(
                "h-1.5 w-1.5 rounded-full",
                connected ? "bg-emerald-400 live-dot" : "bg-slate-600"
              )}
            />
            <span className={connected ? "text-emerald-400" : "text-slate-500"}>
              {connected ? "WS LINK UP" : "WS LINK DOWN"}
            </span>
          </div>
          <span className="text-slate-700">│</span>
          <span>
            NODES: <span className="text-slate-300">{nodeCount.toString().padStart(2, "0")}</span>
          </span>
          <span className="text-slate-700">│</span>
          <span>
            AUTO-SCAN:{" "}
            <span className={autoScanEnabled ? "text-cyan-400" : "text-slate-500"}>
              {autoScanEnabled ? `ON · ${autoScanInterval}m` : "OFF"}
            </span>
          </span>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <span className="hidden md:inline">SUPPLY-CHAIN-OPS v0.1.0</span>
          <span className="text-slate-700 hidden md:inline">│</span>
          <span className="text-slate-300 tabular-nums">{clock}</span>
        </div>
      </div>
    </div>
  );
}
