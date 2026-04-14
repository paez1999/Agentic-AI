"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "@/lib/api";
import { SupplyChainWS } from "@/lib/websocket";
import type {
  FullAnalysisJob,
  PortStatus,
  SimulationEvent,
} from "@/lib/types";

interface PortStore {
  ports: PortStatus[];
  jobs: Record<string, FullAnalysisJob>;
  simulations: SimulationEvent[];
  connected: boolean;
  addPort: (city: string) => Promise<void>;
  removePort: (city: string) => Promise<void>;
  scanAll: () => Promise<void>;
  scanOne: (city: string) => Promise<void>;
  startAnalysis: (city: string) => Promise<string>;
  clearJobsForCity: (city: string) => void;
  removeSimulation: (simId: string) => Promise<void>;
  refreshSimulations: () => Promise<void>;
  simulationsAffecting: (city: string) => SimulationEvent[];
}

const PortStoreContext = createContext<PortStore | null>(null);

export function PortStoreProvider({ children }: { children: React.ReactNode }) {
  const [ports, setPorts] = useState<PortStatus[]>([]);
  const [jobs, setJobs] = useState<Record<string, FullAnalysisJob>>({});
  const [simulations, setSimulations] = useState<SimulationEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<SupplyChainWS | null>(null);

  const mergePort = useCallback((status: PortStatus) => {
    setPorts((prev) => {
      const idx = prev.findIndex((p) => p.city === status.city);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = status;
        return next;
      }
      return [...prev, status];
    });
  }, []);

  useEffect(() => {
    api.ports.list().then(setPorts).catch(console.error);
    api.simulations.list().then(setSimulations).catch(console.error);

    const wsUrl =
      (process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000") + "/ws";
    const ws = new SupplyChainWS(wsUrl);
    wsRef.current = ws;

    ws.on("port.status_updated", (payload) => {
      mergePort(payload.status as PortStatus);
      setConnected(true);
    });

    ws.on("port.added", (payload) => {
      const city = payload.city as string;
      setPorts((prev) =>
        prev.find((p) => p.city === city)
          ? prev
          : [
              ...prev,
              {
                city,
                risk_level: "LOW",
                summary: "Scanning…",
                weather: null,
                scanned_at: null,
              },
            ]
      );
    });

    ws.on("port.removed", (payload) => {
      const city = payload.city as string;
      setPorts((prev) => prev.filter((p) => p.city !== city));
    });

    ws.on("analysis.started", (payload) => {
      const job = payload as unknown as FullAnalysisJob;
      setJobs((prev) => ({ ...prev, [job.job_id]: job }));
    });

    ws.on("analysis.completed", (payload) => {
      const job = payload as unknown as FullAnalysisJob;
      setJobs((prev) => ({
        ...prev,
        [job.job_id]: { ...prev[job.job_id], ...job, status: "completed" },
      }));
    });

    ws.on("analysis.failed", (payload) => {
      const { job_id, city, error } = payload as {
        job_id: string;
        city: string;
        error: string;
      };
      setJobs((prev) => ({
        ...prev,
        [job_id]: {
          ...(prev[job_id] ?? { job_id, city }),
          status: "failed",
          error,
          completed_at: new Date().toISOString(),
        } as FullAnalysisJob,
      }));
    });

    ws.on("simulation.created", (payload) => {
      const sim = payload as unknown as SimulationEvent;
      setSimulations((prev) =>
        prev.find((s) => s.sim_id === sim.sim_id) ? prev : [...prev, sim]
      );
    });

    ws.on("simulation.removed", (payload) => {
      const sim = payload as unknown as SimulationEvent;
      setSimulations((prev) => prev.filter((s) => s.sim_id !== sim.sim_id));
    });

    ws.connect();
    setConnected(true);

    return () => ws.close();
  }, [mergePort]);

  const addPort = useCallback(async (city: string) => {
    await api.ports.add(city);
  }, []);

  const removePort = useCallback(async (city: string) => {
    await api.ports.remove(city);
  }, []);

  const scanAll = useCallback(async () => {
    await api.scan.all();
  }, []);

  const scanOne = useCallback(async (city: string) => {
    await api.scan.one(city);
  }, []);

  const clearJobsForCity = useCallback((city: string) => {
    setJobs((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((id) => {
        if (next[id].city === city) delete next[id];
      });
      return next;
    });
  }, []);

  const startAnalysis = useCallback(async (city: string): Promise<string> => {
    // Clear stale jobs first so the modal transitions to spinner immediately
    clearJobsForCity(city);
    const { job_id } = await api.analysis.start(city);
    setJobs((prev) => ({
      ...prev,
      [job_id]: {
        job_id,
        city,
        status: "running",
        risk_report: null,
        inventory_report: null,
        action_plan: null,
        error: null,
        started_at: new Date().toISOString(),
        completed_at: null,
        has_map: false,
      },
    }));
    return job_id;
  }, [clearJobsForCity]);

  const removeSimulation = useCallback(async (simId: string) => {
    await api.simulations.remove(simId);
  }, []);

  const refreshSimulations = useCallback(async () => {
    const list = await api.simulations.list();
    setSimulations(list);
  }, []);

  const simulationsAffecting = useCallback(
    (city: string) =>
      simulations.filter((s) => s.affected_cities.includes(city)),
    [simulations]
  );

  return (
    <PortStoreContext.Provider
      value={{
        ports,
        jobs,
        simulations,
        connected,
        addPort,
        removePort,
        scanAll,
        scanOne,
        startAnalysis,
        clearJobsForCity,
        removeSimulation,
        refreshSimulations,
        simulationsAffecting,
      }}
    >
      {children}
    </PortStoreContext.Provider>
  );
}

export function usePortStore(): PortStore {
  const ctx = useContext(PortStoreContext);
  if (!ctx) throw new Error("usePortStore must be used inside PortStoreProvider");
  return ctx;
}
