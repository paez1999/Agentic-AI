import type {
  AutoScanConfig,
  CreateSimulationPayload,
  EventTypeMeta,
  FullAnalysisJob,
  PortStatus,
  SimulationEvent,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit,
  timeoutMs = 15000
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`API ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  ports: {
    list: () => request<PortStatus[]>("/api/ports"),
    add: (city: string) =>
      request<{ city: string }>("/api/ports", {
        method: "POST",
        body: JSON.stringify({ city }),
      }),
    remove: (city: string) =>
      request<{ city: string }>(`/api/ports/${encodeURIComponent(city)}`, {
        method: "DELETE",
      }),
  },

  scan: {
    all: () => request<{ message: string }>("/api/scan", { method: "POST" }),
    one: (city: string) =>
      request<{ message: string }>(`/api/scan/${encodeURIComponent(city)}`, {
        method: "POST",
      }),
  },

  analysis: {
    start: (city: string) =>
      request<{ job_id: string; city: string }>(
        `/api/analysis/${encodeURIComponent(city)}`,
        { method: "POST" }
      ),
    get: (jobId: string) =>
      request<FullAnalysisJob>(`/api/analysis/${jobId}`),
  },

  autoScan: {
    get: () => request<AutoScanConfig>("/api/auto-scan"),
    set: (config: AutoScanConfig) =>
      request<AutoScanConfig>("/api/auto-scan", {
        method: "POST",
        body: JSON.stringify(config),
      }),
  },

  simulations: {
    list: () => request<SimulationEvent[]>("/api/simulations"),
    eventTypes: () =>
      request<EventTypeMeta[]>("/api/simulations/event-types"),
    create: (payload: CreateSimulationPayload) =>
      request<SimulationEvent>("/api/simulations", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    remove: (simId: string) =>
      request<SimulationEvent>(`/api/simulations/${simId}`, { method: "DELETE" }),
    clear: () => request<{ removed: number }>("/api/simulations", { method: "DELETE" }),
  },
};
