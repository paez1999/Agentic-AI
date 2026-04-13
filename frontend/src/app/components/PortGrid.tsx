"use client";

import type { PortStatus } from "@/lib/types";
import { PortCard } from "./PortCard";
import { Layers } from "lucide-react";

interface PortGridProps {
  ports: PortStatus[];
  onViewDetails: (port: PortStatus) => void;
  onScan: (city: string) => void;
}

export function PortGrid({ ports, onViewDetails, onScan }: PortGridProps) {
  if (ports.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center">
        <Layers className="h-6 w-6 text-slate-700 mx-auto mb-2" />
        <p className="text-sm text-slate-500 font-mono">NO NODES REGISTERED</p>
        <p className="text-xs text-slate-600 mt-1">Add a port to begin monitoring</p>
      </div>
    );
  }

  // Sort: CRITICAL → HIGH → MEDIUM → LOW
  const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 } as const;
  const sorted = [...ports].sort((a, b) => order[a.risk_level] - order[b.risk_level]);

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="h-3.5 w-3.5 text-cyan-400" />
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">
            Monitored Nodes
          </h2>
          <span className="font-mono text-xs text-slate-600">
            [{ports.length.toString().padStart(2, "0")}]
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {sorted.map((port) => (
          <PortCard
            key={port.city}
            port={port}
            onViewDetails={onViewDetails}
            onScan={onScan}
          />
        ))}
      </div>
    </section>
  );
}
