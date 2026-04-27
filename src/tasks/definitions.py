"""Sequential task flow for the multi-agent PoC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.data.reference_locations import COMPANY_KEY_PORTS, COMPANY_LOGISTIC_HUBS
from src.tools.mock_tools import (
    calculate_alternative_routes,
    check_erp_inventory,
    check_weather_and_news,
)


@dataclass(frozen=True)
class FlowInput:
    product_id: str = "Microchips XYZ"
    key_ports: list[str] | None = None
    logistic_hubs: list[str] | None = None
    simulated_disaster: dict | None = None


def run_sequential_flow(flow_input: FlowInput) -> dict:
    """Run the 3-agent flow for a network of key ports and hubs."""
    # Task 1: Monitor del Entorno (continuous-style scan across 5 key ports)
    key_ports = flow_input.key_ports or COMPANY_KEY_PORTS
    monitor_outputs: list[dict[str, Any]] = []
    for port in key_ports:
        monitor_outputs.append(
            check_weather_and_news(
                port,
                simulated_disaster=flow_input.simulated_disaster,
            )
        )
    high_risk_ports = [item for item in monitor_outputs if item.get("severity") == "high"]
    monitor_summary = {
        "scan_count": len(monitor_outputs),
        "high_risk_ports": [item.get("location") for item in high_risk_ports],
        "avg_risk_score": round(
            sum(float(item.get("geopolitical_risk_score", 0)) for item in monitor_outputs) / max(len(monitor_outputs), 1),
            2,
        ),
    }

    # Task 2: Gestor de Inventario (hub-level static inventory control)
    logistic_hubs = flow_input.logistic_hubs or COMPANY_LOGISTIC_HUBS
    inventory_status = check_erp_inventory(flow_input.product_id)
    hub_inventory: list[dict[str, Any]] = []
    for idx, hub in enumerate(logistic_hubs):
        hub_inventory.append(
            {
                "hub": hub,
                "product_id": flow_input.product_id,
                "stock_days_remaining": max(2, inventory_status["stock_days_remaining"] - idx),
                "current_units": max(200, inventory_status["current_units"] - (idx * 140)),
                "risk_level": "critical" if idx < 2 else "medium",
            }
        )
    impact_report = {
        "product_id": flow_input.product_id,
        "inventory_status": inventory_status,  # global static reference
        "hub_inventory": hub_inventory,
        "upstream_alerts": monitor_outputs,
        "monitor_summary": monitor_summary,
        "estimated_risk": "Posible desbalance de inventario en hubs si persiste la disrupción.",
    }

    # Task 3: Optimizador de Rutas (propose options from safe/low-risk ports to each hub)
    sorted_ports = sorted(monitor_outputs, key=lambda p: p.get("geopolitical_risk_score", 0))
    preferred_origins = [f'Puerto de {item.get("location", "N/A")}' for item in sorted_ports[:2]]
    route_proposals: list[dict[str, Any]] = []
    for hub in logistic_hubs:
        for origin in preferred_origins:
            route_proposals.append(
                calculate_alternative_routes(
                    origin,
                    hub,
                    monitor_alert=sorted_ports[0],
                )
            )

    return {
        "task_1_monitor_output": {"ports": monitor_outputs, "summary": monitor_summary},
        "task_2_inventory_output": impact_report,
        "task_3_route_output": {"proposals": route_proposals},
    }
