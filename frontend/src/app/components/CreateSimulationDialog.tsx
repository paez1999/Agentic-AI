"use client";

import { useEffect, useState } from "react";
import { X, FlaskConical, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { usePortStore } from "../hooks/usePortStore";
import {
  ALL_EVENT_TYPES,
  EVENT_DEFAULT_SEVERITY,
  EVENT_HAZARDS,
  EVENT_ICON,
  EVENT_LABEL,
} from "@/lib/eventIcons";
import type { EventType, RiskLevel } from "@/lib/types";
import { clsx } from "clsx";

interface CreateSimulationDialogProps {
  onClose: () => void;
}

const SEVERITY_OPTIONS: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const SEVERITY_COLORS: Record<RiskLevel, string> = {
  LOW: "border-emerald-500/50 bg-emerald-500/10 text-emerald-200",
  MEDIUM: "border-amber-500/50 bg-amber-500/10 text-amber-200",
  HIGH: "border-orange-500/50 bg-orange-500/10 text-orange-200",
  CRITICAL: "border-red-500/50 bg-red-500/10 text-red-200",
};

export function CreateSimulationDialog({ onClose }: CreateSimulationDialogProps) {
  const { ports, refreshSimulations } = usePortStore();
  const [eventType, setEventType] = useState<EventType>("HURRICANE");
  const [affected, setAffected] = useState<Set<string>>(new Set());
  const [description, setDescription] = useState<string>("");
  const [severity, setSeverity] = useState<RiskLevel | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const defaultSeverity = EVENT_DEFAULT_SEVERITY[eventType];
  const hazards = EVENT_HAZARDS[eventType];

  const toggleCity = (city: string) => {
    setAffected((prev) => {
      const next = new Set(prev);
      if (next.has(city)) next.delete(city);
      else next.add(city);
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (affected.size === 0) {
      setError("Select at least one affected port");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.simulations.create({
        event_type: eventType,
        affected_cities: Array.from(affected),
        description: description.trim() || undefined,
        severity: severity || undefined,
      });
      await refreshSimulations();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-xl max-h-[90vh] overflow-hidden rounded-lg border border-fuchsia-500/40 bg-slate-900 shadow-[0_0_60px_-10px_rgba(217,70,239,0.35)] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-fuchsia-400/60 to-transparent" />

        {/* Header */}
        <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-fuchsia-400" />
            <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-200">
              Inject Simulated Event
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">

          {/* ── Event type picker ── */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mb-2 block">
              Event Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {ALL_EVENT_TYPES.map((et) => (
                <button
                  key={et}
                  type="button"
                  onClick={() => setEventType(et)}
                  title={EVENT_HAZARDS[et]}
                  className={clsx(
                    "relative rounded-lg border px-2 py-3 flex flex-col items-center gap-1.5 transition-all text-center group",
                    eventType === et
                      ? "border-fuchsia-500/70 bg-fuchsia-500/15 shadow-[0_0_12px_-4px_rgba(217,70,239,0.5)]"
                      : "border-slate-800 bg-slate-950/50 hover:border-slate-600 hover:bg-slate-800/60"
                  )}
                >
                  {/* Selected indicator dot */}
                  {eventType === et && (
                    <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-fuchsia-400" />
                  )}
                  <span className="text-2xl leading-none select-none">
                    {EVENT_ICON[et]}
                  </span>
                  <span
                    className={clsx(
                      "font-mono text-[9px] uppercase tracking-wider leading-tight",
                      eventType === et ? "text-fuchsia-200" : "text-slate-500 group-hover:text-slate-300"
                    )}
                  >
                    {EVENT_LABEL[et]}
                  </span>
                </button>
              ))}
            </div>
            {/* Hazard line for selected event */}
            <div className="mt-2.5 flex items-start gap-2 rounded border border-slate-800 bg-slate-950/60 px-3 py-2">
              <span className="text-base leading-none shrink-0 mt-0.5">{EVENT_ICON[eventType]}</span>
              <div>
                <p className="font-mono text-[10px] uppercase tracking-wider text-fuchsia-300 mb-0.5">
                  {EVENT_LABEL[eventType]}
                </p>
                <p className="font-mono text-[10px] text-slate-500 leading-relaxed">
                  <span className="text-slate-400">Hazards:</span> {hazards}
                </p>
              </div>
            </div>
          </div>

          {/* ── Affected ports ── */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mb-2 block">
              Affected Ports
              <span className="ml-2 text-slate-600">
                [{affected.size}/{ports.length} SELECTED]
              </span>
            </label>
            {ports.length === 0 ? (
              <p className="text-xs text-slate-500 font-mono">
                No ports registered. Add one first.
              </p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {ports.map((p) => {
                  const selected = affected.has(p.city);
                  return (
                    <button
                      type="button"
                      key={p.city}
                      onClick={() => toggleCity(p.city)}
                      className={clsx(
                        "rounded border px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider transition-all",
                        selected
                          ? "border-fuchsia-500/60 bg-fuchsia-500/15 text-fuchsia-200 shadow-[0_0_8px_-3px_rgba(217,70,239,0.4)]"
                          : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-600 hover:text-slate-200"
                      )}
                    >
                      {p.city}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* ── Severity override ── */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mb-2 block">
              Severity Override
            </label>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setSeverity("")}
                className={clsx(
                  "rounded border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider transition-colors",
                  severity === ""
                    ? "border-slate-500 bg-slate-700/60 text-slate-200"
                    : "border-slate-800 bg-slate-950/40 text-slate-500 hover:border-slate-600"
                )}
              >
                Default ({defaultSeverity})
              </button>
              {SEVERITY_OPTIONS.map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setSeverity(s)}
                  className={clsx(
                    "rounded border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider transition-colors",
                    severity === s
                      ? SEVERITY_COLORS[s]
                      : "border-slate-800 bg-slate-950/40 text-slate-500 hover:border-slate-600"
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* ── Description ── */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mb-2 block">
              Description
              <span className="ml-2 text-slate-600 normal-case tracking-normal font-sans">
                (optional)
              </span>
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={`e.g. ${EVENT_LABEL[eventType]} approaching from the east coast`}
              className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-100 placeholder:text-slate-600 focus:border-fuchsia-500 focus:outline-none resize-none"
            />
          </div>

          {error && (
            <p className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300 font-mono">
              ERR: {error}
            </p>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-slate-700 bg-slate-900 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-slate-400 hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || affected.size === 0}
              className="inline-flex items-center gap-1.5 rounded border border-fuchsia-500/40 bg-fuchsia-500/15 px-4 py-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-fuchsia-200 hover:bg-fuchsia-500/25 disabled:opacity-40 transition-colors"
            >
              <Zap className="h-3 w-3" />
              {loading ? "Injecting…" : "Inject Event"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
