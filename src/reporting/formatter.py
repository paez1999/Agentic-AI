"""Markdown reporting for human-in-the-loop approval."""

from __future__ import annotations


def format_final_markdown_report(flow_result: dict) -> str:
    monitor_summary = flow_result["task_1_monitor_output"]["summary"]
    inventory = flow_result["task_2_inventory_output"]["inventory_status"]
    proposals = flow_result["task_3_route_output"]["proposals"]
    first = proposals[0]
    route_output = first["options"]
    option_a = next(option for option in route_output if option["id"] == "A")
    option_b = next(option for option in route_output if option["id"] == "B")

    return f"""# Alerta de Cadena de Suministro - Accion Requerida

## Resumen Ejecutivo
Se monitorean `{monitor_summary["scan_count"]}` puertos clave.
Puertos en alto riesgo: `{", ".join(monitor_summary["high_risk_ports"]) if monitor_summary["high_risk_ports"] else "Ninguno"}`.
El producto `{inventory["product_id"]}` cuenta con **{inventory["stock_days_remaining"]} dias** de inventario.

## Riesgo Detectado
- Score geopolítico promedio de red: {monitor_summary["avg_risk_score"]}
- Riesgo operativo: {inventory["risk_level"]}

## Opciones de Mitigacion

### Opcion A - {option_a["name"]}
- ETA: {option_a["eta_days"]} dias
- Costo estimado: USD {option_a["estimated_cost_usd"]:,}
- Nivel de servicio: {option_a["service_level"]}

### Opcion B - {option_b["name"]}
- ETA: {option_b["eta_days"]} dias
- Costo estimado: USD {option_b["estimated_cost_usd"]:,}
- Nivel de servicio: {option_b["service_level"]}

## Trazabilidad de Datos Online
- Agente 1 (monitor): Open-Meteo + GDELT (sin clave paga).
- Agente 3 (rutas): propuestas desde puertos con menor riesgo hacia hubs logísticos.

## Solicitud de Autorizacion (Human-in-the-Loop)
Por favor confirmar autorizacion para ejecutar:

- **Opcion A** (priorizar continuidad, mayor costo), o
- **Opcion B** (priorizar ahorro, mayor tiempo de transito).
"""
