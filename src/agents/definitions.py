"""Agent role definitions for the supply chain PoC."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentProfile:
    name: str
    role: str
    goal: str
    backstory: str


def build_agent_profiles() -> dict[str, AgentProfile]:
    """Return the three agent definitions used by the PoC."""
    return {
        "monitor": AgentProfile(
            name="Monitor del Entorno",
            role="Vigilancia de riesgos externos",
            goal="Detectar disrupciones operativas en puertos clave.",
            backstory="Especialista en monitoreo de riesgo logistico y eventos globales.",
        ),
        "inventory_manager": AgentProfile(
            name="Gestor de Inventario",
            role="Analista de impacto en abastecimiento",
            goal="Estimar impacto en stock y continuidad de produccion.",
            backstory="Analista senior de ERP y niveles de inventario critico.",
        ),
        "route_optimizer": AgentProfile(
            name="Optimizador de Rutas",
            role="Estratega de transporte alternativo",
            goal="Proponer opciones costo/tiempo para mantener suministro.",
            backstory="Experto en TMS, freight-forwarding y escenarios de contingencia.",
        ),
    }
