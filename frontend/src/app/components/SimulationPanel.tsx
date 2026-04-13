"use client";

import { usePortStore } from "../hooks/usePortStore";
import { RiskBadge } from "./RiskBadge";
import { EVENT_ICON, EVENT_LABEL } from "@/lib/eventIcons";
import { FlaskConical, X, Plus } from "lucide-react";
import { clsx } from "clsx";

interface SimulationPanelProps {
  onNewSimulation: () => void;
}

export function SimulationPanel({ onNewSimulation }: SimulationPanelProps) {
  const { simulations, removeSimulation } = usePortStore();

  return (
    <section className="rounded-lg border border-fuchsia-500/30 bg-fuchsia-950/10 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-fuchsia-500/20">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-fuchsia-400" />
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-fuchsia-300">
            Simulation Control
          </h2>
          <span className="font-mono text-xs text-fuchsia-400/70">
            [{simulations.length.toString().padStart(2, "0")} ACTIVE]
          </span>
        </div>
        <button
          onClick={onNewSimulation}
          className="inline-flex items-center gap-1.5 rounded border border-fuchsia-500/40 bg-fuchsia-500/10 px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider text-fuchsia-300 hover:bg-fuchsia-500/20 transition-colors"
        >
          <Plus className="h-3 w-3" />
          Inject Event
        </button>
      </div>

      {simulations.length === 0 ? (
        <div className="px-4 py-5 text-center">
          <p className="font-mono text-xs uppercase tracking-wider text-slate-500">
            No active simulations
          </p>
          <p className="text-xs text-slate-600 mt-1">
            Inject a natural disaster, strike, or attack to test agent response
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-fuchsia-500/10">
          {simulations.map((sim) => (
            <li
              key={sim.sim_id}
              className={clsx(
                "px-4 py-3 flex items-start gap-3",
                sim.severity === "CRITICAL" && "bg-red-500/[0.04]"
              )}
            >
              <span className="text-2xl leading-none shrink-0 pt-0.5">
                {EVENT_ICON[sim.event_type]}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-sm text-slate-100">
                    {EVENT_LABEL[sim.event_type]}
                  </span>
                  <RiskBadge level={sim.severity} compact />
                  <span className="font-mono text-[10px] text-slate-600">
                    #{sim.sim_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {sim.description}
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {sim.affected_cities.map((c) => (
                    <span
                      key={c}
                      className="rounded border border-fuchsia-500/30 bg-fuchsia-500/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-fuchsia-200"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
              <button
                onClick={() => removeSimulation(sim.sim_id)}
                className="shrink-0 rounded p-1 text-slate-500 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                title="End simulation"
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
