export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface WeatherData {
  city: string;
  country: string;
  temperature_c: number;
  feels_like_c: number;
  humidity_pct: number;
  wind_speed_ms: number;
  description: string;
  condition_main: string;
}

export interface Article {
  title: string;
  link: string;
  summary: string;
  source: string;
}

export interface AffectedRoute {
  route_id: string;
  risk_level: string;
  origin: string;
  destination: string;
}

export interface PortStatus {
  city: string;
  risk_level: RiskLevel;
  summary: string;
  weather: WeatherData | null;
  scanned_at: string | null;
  lat: number | null;
  lon: number | null;
  isolated?: boolean;
  affected_routes?: AffectedRoute[] | null;
  local_news?: Article[] | null;
  news_reasoning?: string | null;
  country_code?: string | null;
}

export type RouteType = "maritime" | "terrestrial" | "air";

export interface RouteStatus {
  route_id: string;
  origin: string;
  destination: string;
  route_type: RouteType;
  risk_level: RiskLevel;
  summary: string;
  origin_weather: WeatherData | null;
  destination_weather: WeatherData | null;
  scanned_at: string | null;
  waypoints?: Array<[number, number]> | null;
  planner_rationale?: string | null;
  avoid_used?: string[] | null;
}

export interface FullAnalysisJob {
  job_id: string;
  city: string;
  status: "pending" | "running" | "completed" | "failed";
  risk_report: string | null;
  inventory_report: string | null;
  action_plan: string | null;
  has_map: boolean;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface WSEvent {
  event: string;
  payload: Record<string, unknown>;
}

export interface AutoScanConfig {
  enabled: boolean;
  interval_minutes: number;
}

export interface CoordSimulationPayload {
  lat: number;
  lon: number;
  radius_km: number;
  event_type: EventType;
  description?: string;
  severity?: RiskLevel;
}

export type EventType =
  | "HURRICANE"
  | "EARTHQUAKE"
  | "TSUNAMI"
  | "WILDFIRE"
  | "FLOOD"
  | "VOLCANIC_ERUPTION"
  | "NUCLEAR_STRIKE"
  | "CYBERATTACK"
  | "PORT_STRIKE"
  | "ARMED_CONFLICT"
  | "PANDEMIC"
  | "CUSTOM";

export interface SimulationEvent {
  sim_id: string;
  event_type: EventType;
  severity: RiskLevel;
  affected_cities: string[];
  description: string;
  polygon: number[][] | null;
  coordinates: [number, number] | null; // [lat, lon]
  radius_km: number | null;
  created_at: string;
}

export interface EventTypeMeta {
  event_type: EventType;
  default_severity: RiskLevel;
  headline: string;
  hazards: string;
}

export interface CreateSimulationPayload {
  event_type: EventType;
  affected_cities: string[];
  description?: string;
  severity?: RiskLevel;
}
