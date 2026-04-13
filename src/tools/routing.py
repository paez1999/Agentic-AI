import json
import os
import httpx

from src.core.tool import Tool

COORDS = {
    "veracruz": [-96.1342, 19.1738],
    "houston": [-95.3698, 29.7604],
    "tampa": [-82.4572, 27.9506],
    "mexico city": [-99.1332, 19.4326],
}

ORS_BASE = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


def _resolve_coords(location: str) -> list:
    key = location.lower().strip()
    for k, v in COORDS.items():
        if k in key or key in k:
            return v
    raise ValueError(f"Unknown location: '{location}'. Known: {list(COORDS.keys())}")


def get_route(origin: str, destination: str) -> str:
    try:
        api_key = os.environ["ORS_API_KEY"]
        origin_coords = _resolve_coords(origin)
        dest_coords = _resolve_coords(destination)

        body = {"coordinates": [origin_coords, dest_coords]}
        headers = {"Authorization": api_key, "Content-Type": "application/json"}

        response = httpx.post(ORS_BASE, json=body, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        summary = data["features"][0]["properties"]["summary"]
        result = {
            "origin": origin,
            "destination": destination,
            "distance_km": round(summary["distance"] / 1000, 1),
            "duration_hours": round(summary["duration"] / 3600, 1),
            "geometry": data["features"][0]["geometry"]["coordinates"],
        }
        return json.dumps(result, ensure_ascii=False)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except KeyError as e:
        return json.dumps({"error": f"Missing environment variable: {e}"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"ORS API error {e.response.status_code}", "detail": e.response.text[:200]})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


def get_alternative_route(origin: str, destination: str, avoid_polygon) -> str:
    try:
        api_key = os.environ["ORS_API_KEY"]
        origin_coords = _resolve_coords(origin)
        dest_coords = _resolve_coords(destination)

        # LLMs sometimes serialize arrays as JSON strings — parse if needed
        if isinstance(avoid_polygon, str):
            avoid_polygon = json.loads(avoid_polygon)

        # Auto-close polygon if needed
        if avoid_polygon and avoid_polygon[0] != avoid_polygon[-1]:
            avoid_polygon = avoid_polygon + [avoid_polygon[0]]

        body = {
            "coordinates": [origin_coords, dest_coords],
            "options": {
                "avoid_polygons": {
                    "type": "Polygon",
                    "coordinates": [avoid_polygon],
                }
            },
        }
        headers = {"Authorization": api_key, "Content-Type": "application/json"}

        response = httpx.post(ORS_BASE, json=body, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        summary = data["features"][0]["properties"]["summary"]
        result = {
            "origin": origin,
            "destination": destination,
            "route_type": "alternative (avoids risk zone)",
            "distance_km": round(summary["distance"] / 1000, 1),
            "duration_hours": round(summary["duration"] / 3600, 1),
            "avoided_polygon_points": len(avoid_polygon),
            "geometry": data["features"][0]["geometry"]["coordinates"],
        }
        return json.dumps(result, ensure_ascii=False)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except KeyError as e:
        return json.dumps({"error": f"Missing environment variable: {e}"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"ORS API error {e.response.status_code}", "detail": e.response.text[:200]})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


def send_alert(message: str, severity: str) -> str:
    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if severity not in valid_severities:
        return json.dumps({"error": f"Invalid severity '{severity}'. Must be one of {sorted(valid_severities)}"})
    line = "=" * 60
    print(f"\n{line}\n[ALERT - {severity}] {message}\n{line}\n")
    return json.dumps({"status": "alert_sent", "severity": severity, "message": message})


def confirm_action(action: str) -> str:
    print(f"[ACTION CONFIRMED] {action}")
    return json.dumps({"status": "confirmed", "action": action, "result": "Execution OK"})


ROUTE_TOOL = Tool(
    name="get_route",
    description="Get the current route between two locations (land routes only). Returns distance in km and duration in hours.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Origin city name"},
            "destination": {"type": "string", "description": "Destination city name"},
        },
        "required": ["origin", "destination"],
    },
    fn=get_route,
)

ALT_ROUTE_TOOL = Tool(
    name="get_alternative_route",
    description="Get an alternative route avoiding a risk zone polygon (land routes only). avoid_polygon is a list of [longitude, latitude] pairs forming a closed polygon.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "destination": {"type": "string"},
            "avoid_polygon": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "number"}},
                "description": "List of [lon, lat] pairs forming the exclusion polygon",
            },
        },
        "required": ["origin", "destination", "avoid_polygon"],
    },
    fn=get_alternative_route,
)

ALERT_TOOL = Tool(
    name="send_alert",
    description="Send a structured alert notification. severity must be one of: LOW, MEDIUM, HIGH, CRITICAL.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        },
        "required": ["message", "severity"],
    },
    fn=send_alert,
)

CONFIRM_TOOL = Tool(
    name="confirm_action",
    description="Confirm and record an action decision. Returns 'Ejecucion OK'.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Description of the action being confirmed",
            }
        },
        "required": ["action"],
    },
    fn=confirm_action,
)
