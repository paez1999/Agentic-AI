"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Loader2, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { usePortStore } from "../hooks/usePortStore";
import type { AutoScanConfig } from "@/lib/types";
import { clsx } from "clsx";

interface AutoScanControlsProps {
  onConfigChange?: (config: AutoScanConfig) => void;
}

export function AutoScanControls({ onConfigChange }: AutoScanControlsProps = {}) {
  const { scanAll } = usePortStore();
  const [config, setConfig] = useState<AutoScanConfig>({
    enabled: false,
    interval_minutes: 15,
  });
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    api.autoScan
      .get()
      .then((c) => {
        setConfig(c);
        onConfigChange?.(c);
      })
      .catch(console.error);
  }, [onConfigChange]);

  const updateAutoScan = async (next: AutoScanConfig) => {
    const result = await api.autoScan.set(next);
    setConfig(result);
    onConfigChange?.(result);
  };

  const handleScanNow = async () => {
    setScanning(true);
    try {
      await scanAll();
    } finally {
      setTimeout(() => setScanning(false), 2000);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={handleScanNow}
        disabled={scanning}
        className={clsx(
          "inline-flex items-center gap-1.5 rounded border px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider transition-colors",
          scanning
            ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
            : "border-slate-700 bg-slate-900/60 text-slate-300 hover:border-cyan-500/40 hover:text-cyan-300"
        )}
      >
        {scanning ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <RefreshCw className="h-3 w-3" />
        )}
        {scanning ? "Scanning" : "Scan Now"}
      </button>

      <div
        className={clsx(
          "inline-flex items-center gap-2 rounded border px-2 py-1 font-mono text-[11px] uppercase tracking-wider transition-colors",
          config.enabled
            ? "border-cyan-500/40 bg-cyan-500/5 text-cyan-300"
            : "border-slate-700 bg-slate-900/60 text-slate-400"
        )}
      >
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <Zap className={clsx("h-3 w-3", config.enabled ? "text-cyan-400" : "text-slate-500")} />
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) =>
              updateAutoScan({ ...config, enabled: e.target.checked })
            }
            className="h-3 w-3 rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-0 focus:ring-offset-0"
          />
          Auto
        </label>
        <select
          value={config.interval_minutes}
          onChange={(e) =>
            updateAutoScan({ ...config, interval_minutes: Number(e.target.value) })
          }
          className="bg-transparent border-l border-slate-700 pl-2 font-mono text-[11px] uppercase tracking-wider focus:outline-none cursor-pointer"
        >
          {[5, 10, 15, 30, 60].map((v) => (
            <option key={v} value={v} className="bg-slate-900">
              {v}m
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
