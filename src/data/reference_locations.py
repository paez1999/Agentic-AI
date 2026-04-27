"""Reference locations to improve geopolitical news hit-rate."""

from __future__ import annotations

IMPORTANT_PORTS = [
    "Shanghai",
    "Singapore",
    "Rotterdam",
    "Ningbo-Zhoushan",
    "Shenzhen",
    "Busan",
    "Hong Kong",
    "Los Angeles",
    "Long Beach",
    "Hamburg",
    "Antwerp-Bruges",
    "Dubai (Jebel Ali)",
    "Santos",
    "Tanger Med",
    "Port Klang",
    "Piraeus",
    "New York-New Jersey",
    "Qingdao",
    "Tianjin",
    "Colombo",
]

IMPORTANT_ORIGINS = [
    "Puerto de Shanghai",
    "Puerto de Singapore",
    "Puerto de Rotterdam",
    "Puerto de Ningbo-Zhoushan",
    "Puerto de Shenzhen",
    "Puerto de Busan",
    "Puerto de Los Angeles",
    "Puerto de Long Beach",
    "Puerto de Hamburg",
    "Puerto de Jebel Ali",
]

IMPORTANT_DESTINATIONS = [
    "Planta Monterrey",
    "Planta Queretaro",
    "Planta Guadalajara",
    "Hub logístico Dallas",
    "Hub logístico Chicago",
    "Hub logístico Frankfurt",
    "Hub logístico Amsterdam",
    "Hub logístico Dubai",
    "Hub logístico Singapore",
    "Centro de distribución Sao Paulo",
]

IMPORTANT_PRODUCTS = [
    "Microchips XYZ",
    "Semiconductores automotrices",
    "Baterías de litio",
    "Componentes electrónicos de potencia",
    "Sensores industriales",
]

GEOPOLITICAL_REGIONS = [
    "Global",
    "Middle East",
    "Red Sea",
    "Europe",
    "East Asia",
    "South China Sea",
    "Black Sea",
    "North America",
    "Latin America",
]

# Company network model (new operating mode)
COMPANY_KEY_PORTS = [
    "Shanghai",
    "Singapore",
    "Rotterdam",
    "Dubai (Jebel Ali)",
    "Los Angeles",
]

COMPANY_LOGISTIC_HUBS = [
    "Hub logístico Singapore",
    "Hub logístico Dubai",
    "Hub logístico Frankfurt",
    "Hub logístico Chicago",
    "Centro de distribución Sao Paulo",
]

DISASTER_SCENARIOS = {
    "Sin simulación": {
        "enabled": False,
        "region": "Global",
        "event": "Sin evento simulado",
        "risk_boost": 0,
    },
    "Crisis en Estrecho de Ormuz": {
        "enabled": True,
        "region": "Middle East",
        "event": "Escalada militar y riesgo de interrupción en el Estrecho de Ormuz.",
        "risk_boost": 40,
    },
    "Ataques en Mar Rojo": {
        "enabled": True,
        "region": "Red Sea",
        "event": "Ataques a buques comerciales en corredor Mar Rojo - Bab el-Mandeb.",
        "risk_boost": 35,
    },
    "Sanciones y bloqueos en Europa": {
        "enabled": True,
        "region": "Europe",
        "event": "Nuevas sanciones y bloqueos afectan flujos logísticos europeos.",
        "risk_boost": 25,
    },
}
