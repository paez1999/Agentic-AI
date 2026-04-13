import json

from src.core.tool import Tool

INVENTORY = {
    "veracruz": {
        "center": "Centro de Distribucion Veracruz",
        "location": "Veracruz, Mexico",
        "products": [
            {"name": "Electronica de consumo", "category": "electronics", "stock_units": 12000, "value_usd": 800000},
            {"name": "Materias primas industriales", "category": "raw_materials", "stock_units": 45000, "value_usd": 1200000},
        ],
    },
    "houston": {
        "center": "Centro de Distribucion Houston",
        "location": "Houston, TX, USA",
        "products": [
            {"name": "Electronica de consumo", "category": "electronics", "stock_units": 8000, "value_usd": 500000},
            {"name": "Productos perecederos", "category": "perishables", "stock_units": 3000, "value_usd": 300000},
        ],
    },
    "tampa": {
        "center": "Centro de Distribucion Tampa",
        "location": "Tampa, FL, USA",
        "products": [
            {"name": "Productos perecederos", "category": "perishables", "stock_units": 5000, "value_usd": 400000},
            {"name": "Materias primas industriales", "category": "raw_materials", "stock_units": 18000, "value_usd": 600000},
        ],
    },
}

ROUTES = [
    {"id": "R001", "type": "maritime", "origin": "Veracruz", "destination": "Houston",
     "carrier": "Maersk Line", "eta_days": 3, "cargo_value_usd": 1500000, "status": "in_transit"},
    {"id": "R002", "type": "land", "origin": "Houston", "destination": "Tampa",
     "carrier": "JB Hunt", "eta_days": 2, "cargo_value_usd": 800000, "status": "in_transit"},
    {"id": "R003", "type": "maritime", "origin": "Tampa", "destination": "Veracruz",
     "carrier": "CMA CGM", "eta_days": 5, "cargo_value_usd": 600000, "status": "scheduled"},
]


def get_inventory(location: str) -> str:
    key = location.lower().strip()
    # Fuzzy match
    for k in INVENTORY:
        if k in key or key in k:
            return json.dumps(INVENTORY[k], ensure_ascii=False)
    available = list(INVENTORY.keys())
    return json.dumps({"error": f"Location '{location}' not found. Available: {available}"})


def get_active_routes() -> str:
    return json.dumps(ROUTES, ensure_ascii=False)


INVENTORY_TOOL = Tool(
    name="get_inventory",
    description="Get inventory for a distribution center location. Available locations: Veracruz, Houston, Tampa.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Distribution center location name, e.g. 'Veracruz' or 'Houston'",
            }
        },
        "required": ["location"],
    },
    fn=get_inventory,
)

ROUTES_TOOL = Tool(
    name="get_active_routes",
    description="Get all active supply chain routes including origin, destination, carrier, ETA, and cargo value.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    fn=get_active_routes,
)
