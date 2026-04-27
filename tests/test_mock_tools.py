from src.tools.mock_tools import (
    calculate_alternative_routes,
    check_erp_inventory,
    check_weather_and_news,
)


def test_weather_tool_returns_high_severity_alert():
    result = check_weather_and_news("Shanghai")
    assert "location" in result
    assert result["severity"] in {"low", "medium", "high"}
    assert "expected_delay_days" in result
    assert "source" in result
    assert "geopolitical_risk_score" in result
    assert "geopolitical_articles" in result
    assert "queries_used" in result


def test_inventory_tool_returns_low_stock_signal():
    result = check_erp_inventory("Microchips XYZ")
    assert result["product_id"] == "Microchips XYZ"
    assert result["stock_days_remaining"] == 5
    assert result["risk_level"] == "critical"


def test_routes_tool_returns_two_alternative_options():
    result = calculate_alternative_routes(
        "A",
        "B",
        monitor_alert={
            "severity": "high",
            "expected_delay_days": 4,
            "news_signal_count": 3,
            "geopolitical_risk_score": 80,
        },
    )
    assert result["origin"] == "A"
    assert result["destination"] == "B"
    assert len(result["options"]) == 2
    assert result["options"][0]["id"] == "A"
    assert result["options"][1]["id"] == "B"
    assert "online_context_used" in result
    assert "route_map" in result
    assert "paths" in result["route_map"]
    assert len(result["route_map"]["paths"]) == 2
