"use client";

import { useEffect, useState } from "react";
import type { FullAnalysisJob, PortStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";
import { X, Play, Loader2, Terminal, Trash2, FlaskConical, RefreshCw, Radar, Map } from "lucide-react";
import { usePortStore } from "../hooks/usePortStore";
import { EVENT_ICON, EVENT_LABEL } from "@/lib/eventIcons";
import { clsx } from "clsx";

interface ReportModalProps {
  port: PortStatus;
  onClose: () => void;
}

type Tab = "risk" | "inventory" | "action" | "map";

export function ReportModal({ port, onClose }: ReportModalProps) {
  const { jobs, startAnalysis, scanOne, removePort, simulationsAffecting } = usePortStore();
  const activeSims = simulationsAffecting(port.city);
  const [activeTab, setActiveTab] = useState<Tab>("risk");
  const [jobId, setJobId] = useState<string | null>(null);

  const job: FullAnalysisJob | undefined = jobId
    ? jobs[jobId]
    : Object.values(jobs)
        .filter((j) => j.city === port.city)
        .sort((a, b) => (b.started_at ?? "").localeCompare(a.started_at ?? ""))[0];

  const isRunning = job?.status === "running";

  const handleRunAnalysis = async () => {
    setJobId(null); // clear local ref so modal shows spinner immediately
    const id = await startAnalysis(port.city);
    setJobId(id);
  };

  const handleQuickScan = () => {
    scanOne(port.city).catch(console.error);
  };

  const handleRemove = async () => {
    if (
      confirm(`Remove ${port.city} from monitored nodes? This cannot be undone.`)
    ) {
      await removePort(port.city);
      onClose();
    }
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const textTabs: { key: Tab; label: string; content: string | null | undefined }[] = [
    { key: "risk", label: "Risk", content: job?.risk_report },
    { key: "inventory", label: "Inventory", content: job?.inventory_report },
    { key: "action", label: "Action Plan", content: job?.action_plan },
  ];

  const tabs: { key: Tab; label: string }[] = [
    ...textTabs,
    ...(job?.has_map ? [{ key: "map" as Tab, label: "Route Map" }] : []),
  ];

  const activeContent = textTabs.find((t) => t.key === activeTab)?.content;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-lg border border-cyan-500/30 bg-slate-900 shadow-[0_0_60px_-10px_rgba(34,211,238,0.25)] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* top accent line */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent" />

        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-slate-800 px-5 py-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-slate-500">
              <Terminal className="h-3 w-3" />
              Node Inspection
              <span className="text-slate-700">·</span>
              <span className="text-slate-600">
                {port.city.substring(0, 3).toUpperCase()}-
                {(port.city.length * 7).toString().padStart(3, "0")}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <h2 className="text-xl font-semibold text-slate-100">{port.city}</h2>
              <RiskBadge level={port.risk_level} />
              {port.weather && (
                <span className="font-mono text-xs text-slate-500">
                  {port.weather.country} · {port.weather.temperature_c.toFixed(1)}°C
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={handleRemove}
              className="rounded p-1.5 text-slate-500 hover:text-red-300 hover:bg-red-500/10 transition-colors"
              title="Remove node"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={onClose}
              className="rounded p-1.5 text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Quick summary */}
        <div className="border-b border-slate-800 px-5 py-3 bg-slate-950/40">
          <p className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mb-1">
            Latest Assessment
          </p>
          <p className="text-sm text-slate-300 leading-relaxed">{port.summary}</p>
        </div>

        {/* Active simulations */}
        {activeSims.length > 0 && (
          <div className="border-b border-fuchsia-500/30 bg-fuchsia-500/[0.06] px-5 py-3">
            <div className="flex items-center gap-2 mb-2">
              <FlaskConical className="h-3.5 w-3.5 text-fuchsia-400" />
              <p className="font-mono text-[10px] uppercase tracking-wider text-fuchsia-300">
                Active Simulations
              </p>
            </div>
            <ul className="space-y-1.5">
              {activeSims.map((sim) => (
                <li key={sim.sim_id} className="flex items-start gap-2">
                  <span className="text-base leading-none shrink-0">
                    {EVENT_ICON[sim.event_type]}
                  </span>
                  <div className="min-w-0 flex-1">
                    <span className="font-medium text-xs text-slate-200">
                      {EVENT_LABEL[sim.event_type]}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500 ml-2">
                      #{sim.sim_id} · {sim.severity}
                    </span>
                    <p className="text-[11px] text-slate-400 leading-snug">
                      {sim.description}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Analysis controls — state-aware */}
        {(!job || job.status === "completed" || job.status === "failed") && (
          <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between gap-3">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
                {job?.status === "completed" ? "Analysis Complete" : "Deep Analysis"}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {job?.status === "completed"
                  ? "Run a new analysis or trigger a quick lightweight scan"
                  : "Run the full 3-phase pipeline: Risk · Inventory · Action Plan"}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {/* Quick scan always available */}
              <button
                onClick={handleQuickScan}
                className="inline-flex items-center gap-1.5 rounded border border-slate-600 bg-slate-800/60 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-slate-300 hover:border-cyan-500/40 hover:text-cyan-300 transition-colors"
                title="Lightweight scan: weather + news → risk badge update"
              >
                <Radar className="h-3.5 w-3.5" />
                Quick Scan
              </button>
              {/* Full analysis */}
              <button
                onClick={handleRunAnalysis}
                className="inline-flex items-center gap-2 rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-cyan-300 hover:bg-cyan-500/20 transition-colors"
              >
                {job?.status === "completed" ? (
                  <RefreshCw className="h-3.5 w-3.5" />
                ) : (
                  <Play className="h-3.5 w-3.5" />
                )}
                {job?.status === "completed" ? "Re-run" : "Execute"}
              </button>
            </div>
          </div>
        )}

        {isRunning && (
          <div className="relative overflow-hidden border-b border-cyan-500/30 bg-cyan-500/5 px-5 py-3">
            <div className="absolute inset-0 scan-sweep pointer-events-none" />
            <div className="relative flex items-center gap-3">
              <Loader2 className="h-4 w-4 text-cyan-300 animate-spin" />
              <div>
                <p className="font-mono text-xs text-cyan-300 uppercase tracking-wider">
                  Pipeline Running
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Executing 3-phase analysis · ~60s · results stream via WebSocket
                </p>
              </div>
            </div>
          </div>
        )}

        {job?.status === "failed" && (
          <div className="border-b border-red-500/30 bg-red-500/5 px-5 py-2">
            <p className="font-mono text-[10px] text-red-300 uppercase tracking-wider">
              Last run failed: <span className="text-slate-400 normal-case tracking-normal">{job.error}</span>
            </p>
          </div>
        )}

        {/* Tabs */}
        {job?.status === "completed" && (
          <>
            <div className="flex border-b border-slate-800 px-5 gap-1 bg-slate-950/40">
              {tabs.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  className={clsx(
                    "px-3 py-2 font-mono text-[11px] uppercase tracking-wider border-b-2 transition-colors",
                    activeTab === t.key
                      ? "border-cyan-400 text-cyan-300"
                      : "border-transparent text-slate-500 hover:text-slate-300"
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="overflow-y-auto flex-1 bg-slate-950/60">
              {activeTab === "map" ? (
                <iframe
                  src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/analysis/${job?.job_id}/map`}
                  className="w-full border-0"
                  style={{ height: "520px" }}
                  sandbox="allow-scripts allow-same-origin"
                  title="Route Map"
                />
              ) : (
                <div className="px-5 py-4">
                  <pre className="whitespace-pre-wrap font-mono text-[12px] text-slate-300 leading-relaxed">
                    {activeContent ?? "— no data —"}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}

        {!job && !isRunning && (
          <div className="flex-1 px-5 py-8 text-center">
            <Terminal className="h-6 w-6 text-slate-700 mx-auto mb-2" />
            <p className="font-mono text-xs uppercase tracking-wider text-slate-600">
              No Analysis Data
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Execute a deep analysis or run a quick scan above
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
