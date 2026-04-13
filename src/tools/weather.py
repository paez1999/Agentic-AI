import json
import os
import httpx

from src.core.tool import Tool


def get_weather(city: str) -> str:
    try:
        api_key = os.environ["OWM_API_KEY"]
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric", "lang": "es"}
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        result = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "humidity_pct": data["main"]["humidity"],
            "wind_speed_ms": data["wind"]["speed"],
            "description": data["weather"][0]["description"],
            "condition_id": data["weather"][0]["id"],
            "condition_main": data["weather"][0]["main"],
        }
        return json.dumps(result, ensure_ascii=False)
    except KeyError as e:
        return json.dumps({"error": f"Missing environment variable: {e}"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"API error {e.response.status_code}", "detail": e.response.text[:200]})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


WEATHER_TOOL = Tool(
    name="get_weather",
    description="Get current weather conditions for a city. Returns temperature, humidity, wind speed, and weather description.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'Veracruz' or 'Houston'",
            }
        },
        "required": ["city"],
    },
    fn=get_weather,
)
