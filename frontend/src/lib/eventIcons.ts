import type { EventType, RiskLevel } from "./types";

export const EVENT_ICON: Record<EventType, string> = {
  HURRICANE: "🌀",
  EARTHQUAKE: "💥",
  TSUNAMI: "🌊",
  WILDFIRE: "🔥",
  FLOOD: "💧",
  VOLCANIC_ERUPTION: "🌋",
  NUCLEAR_STRIKE: "☢️",
  CYBERATTACK: "💻",
  PORT_STRIKE: "✊",
  ARMED_CONFLICT: "⚔️",
  PANDEMIC: "🦠",
  CUSTOM: "⚡",
};

export const EVENT_LABEL: Record<EventType, string> = {
  HURRICANE: "Hurricane",
  EARTHQUAKE: "Earthquake",
  TSUNAMI: "Tsunami",
  WILDFIRE: "Wildfire",
  FLOOD: "Flood",
  VOLCANIC_ERUPTION: "Volcanic Eruption",
  NUCLEAR_STRIKE: "Nuclear Strike",
  CYBERATTACK: "Cyberattack",
  PORT_STRIKE: "Port Strike",
  ARMED_CONFLICT: "Armed Conflict",
  PANDEMIC: "Pandemic",
  CUSTOM: "Custom Event",
};

export const EVENT_DEFAULT_SEVERITY: Record<EventType, RiskLevel> = {
  HURRICANE: "CRITICAL",
  EARTHQUAKE: "HIGH",
  TSUNAMI: "CRITICAL",
  WILDFIRE: "HIGH",
  FLOOD: "HIGH",
  VOLCANIC_ERUPTION: "HIGH",
  NUCLEAR_STRIKE: "CRITICAL",
  CYBERATTACK: "HIGH",
  PORT_STRIKE: "MEDIUM",
  ARMED_CONFLICT: "CRITICAL",
  PANDEMIC: "HIGH",
  CUSTOM: "MEDIUM",
};

export const EVENT_HAZARDS: Record<EventType, string> = {
  HURRICANE: "storm surge, 200+ km/h winds, flooding, port closure",
  EARTHQUAKE: "structural damage, infrastructure collapse, aftershocks",
  TSUNAMI: "coastal flooding, port facilities destroyed, mass evacuation",
  WILDFIRE: "smoke closure, evacuation, road blockage",
  FLOOD: "loading docks inoperable, transport network cut",
  VOLCANIC_ERUPTION: "air/sea traffic shutdown, ash contamination",
  NUCLEAR_STRIKE: "blast damage, radiation contamination, total port denial",
  CYBERATTACK: "terminal operating system offline, customs paralysed",
  PORT_STRIKE: "loading operations halted indefinitely",
  ARMED_CONFLICT: "shipping lanes unsafe, sanctions risk, workforce displacement",
  PANDEMIC: "workforce shortage, mandatory ship quarantines",
  CUSTOM: "see description",
};

// Ordered list for the picker grid
export const ALL_EVENT_TYPES: EventType[] = [
  "HURRICANE",
  "EARTHQUAKE",
  "TSUNAMI",
  "WILDFIRE",
  "FLOOD",
  "VOLCANIC_ERUPTION",
  "NUCLEAR_STRIKE",
  "CYBERATTACK",
  "PORT_STRIKE",
  "ARMED_CONFLICT",
  "PANDEMIC",
  "CUSTOM",
];
