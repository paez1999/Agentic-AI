"use client";

import { useState } from "react";
import type { PortStatus, AutoScanConfig } from "@/lib/types";
import { usePortStore } from "./hooks/usePortStore";
import { PortGrid } from "./components/PortGrid";
import { AlertPanel } from "./components/AlertPanel";
import { ReportModal } from "./components/ReportModal";
import { AddPortDialog } from "./components/AddPortDialog";
import { AutoScanControls } from "./components/AutoScanControls";
import { MetricsBar } from "./components/MetricsBar";
import { StatusBar } from "./components/StatusBar";
import { SimulationPanel } from "./components/SimulationPanel";
import { CreateSimulationDialog } from "./components/CreateSimulationDialog";
import { Plus, Activity } from "lucide-react";

export default function DashboardPage() {
  const { ports, connected, scanOne } = usePortStore();
  const [selectedPort, setSelectedPort] = useState<PortStatus | null>(null);
  const [showAddPort, setShowAddPort] = useState(false);
  const [showCreateSim, setShowCreateSim] = useState(false);
  const [autoScan, setAutoScan] = useState<AutoScanConfig>({
    enabled: false,
    interval_minutes: 15,
  });

  const selectedLive =
    selectedPort && ports.find((p) => p.city === selectedPort.city);

  return (
    <div className="min-h-screen text-slate-100 pb-10">
      {/* Top bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded border border-cyan-500/30 bg-cyan-500/10">
              <Activity className="h-4 w-4 text-cyan-400 live-dot rounded-full" />
            </div>
            <div>
              <h1 className="font-mono text-sm font-bold text-slate-100 leading-none tracking-wide">
                SUPPLY<span className="text-cyan-400">·</span>CHAIN<span className="text-cyan-400">·</span>OPS
              </h1>
              <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
                Risk Monitoring Station
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <AutoScanControls onConfigChange={setAutoScan} />
            <button
              onClick={() => setShowAddPort(true)}
              className="inline-flex items-center gap-1.5 rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-cyan-300 hover:bg-cyan-500/20 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Node
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        <MetricsBar ports={ports} />
        <AlertPanel ports={ports} onViewDetails={setSelectedPort} />
        <SimulationPanel onNewSimulation={() => setShowCreateSim(true)} />
        <PortGrid
          ports={ports}
          onViewDetails={setSelectedPort}
          onScan={(city) => {
            scanOne(city).catch(console.error);
          }}
        />
      </main>

      {/* Modals */}
      {selectedLive && (
        <ReportModal port={selectedLive} onClose={() => setSelectedPort(null)} />
      )}
      {showAddPort && <AddPortDialog onClose={() => setShowAddPort(false)} />}
      {showCreateSim && (
        <CreateSimulationDialog onClose={() => setShowCreateSim(false)} />
      )}

      <StatusBar
        connected={connected}
        autoScanEnabled={autoScan.enabled}
        autoScanInterval={autoScan.interval_minutes}
        nodeCount={ports.length}
      />
    </div>
  );
}
