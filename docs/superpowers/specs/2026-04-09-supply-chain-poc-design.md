# PoC Multi-Agente Supply Chain — Design Spec
**Date:** 2026-04-09

## Vision

PoC de un sistema multi-agente de supply chain donde cada agente es un LLM con herramientas reales. El sistema detecta riesgos climaticos/geopoliticos, evalua impacto en inventario y calcula rutas alternativas — de forma completamente autonoma.

---

## Constraints

- **No frameworks de agentes** (no CrewAI, no LangChain agents). El loop agentivo se construye desde cero.
- **LLM:** Groq API (free tier) — modelo `llama-3.3-70b-versatile`
- **Datos reales:** Agents 1 y 3 usan APIs reales gratuitas
- **Datos mock:** Solo Agent 2 (InventoryManager)
- **Costo:** $0 — todas las APIs en free tier sin tarjeta de credito (excepto ORS que tiene free tier con registro)

---

## Arquitectura

### Core: Clase `Agent` con loop agentivo

Cada agente es una instancia de `Agent` con:
- `system_prompt`: define rol, objetivo y comportamiento
- `tools: list[Tool]`: herramientas disponibles
- `run(context: str) -> AgentResult`: ejecuta el loop completo

**Loop agentivo:**
```
run(context):
  messages = [system_prompt, user(context)]
  loop:
    response = groq_client.chat(messages, tools=self.tools)
    if response.finish_reason == "tool_calls":
      for call in response.tool_calls:
        result = self._execute_tool(call.name, call.args)
        messages.append(tool_result(result))
      continue
    if response.finish_reason == "stop":
      return AgentResult(content=response.content, messages=messages)
```

El LLM decide **cuando y como** llamar a las tools. No hay logica condicional que dicte el orden.

### Clase `Tool`

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema
    fn: Callable
```

Los tools se registran como JSON schema en la llamada al LLM (Groq function calling).

---

## Agentes

### Agent 1 — RiskMonitor
**Rol:** Detecta riesgos climaticos y geopoliticos que puedan afectar la cadena de suministro.

**Tools:**
- `get_weather(city: str)` — OpenWeatherMap API (free tier, API key requerida, gratuita)
  - Retorna: temperatura, condiciones, alertas meteorologicas
- `get_news(query: str)` — RSS feed publico (sin API key)
  - Fuente: `https://feeds.bbci.co.uk/news/world/rss.xml` (BBC World, estable y publico)
  - Retorna: titulares relevantes al query (filtrados por palabras clave)

**Output:** Reporte de riesgos con severidad (LOW/MEDIUM/HIGH/CRITICAL) y ciudades afectadas.

---

### Agent 2 — InventoryManager
**Rol:** Evalua el impacto del riesgo detectado sobre el inventario y rutas activas.

**Tools (mock):**
- `get_inventory(location: str)` — retorna JSON con productos, stock y centro de distribucion
- `get_active_routes()` — retorna JSON con rutas activas, proveedores y ETAs

**Mock data incluye:**
- Centros de distribucion: Veracruz MX, Houston TX, Tampa FL
- Productos: electronicos, materias primas, perecederos
- Rutas: maritimas y terrestres entre los centros

**Output:** Lista de activos en riesgo (productos/rutas) con impacto estimado (dias de retraso, valor en riesgo).

---

### Agent 3 — RouteOptimizer
**Rol:** Calcula rutas alternativas reales y emite el plan de accion final.

**Tools:**
- `get_route(origin: str, destination: str)` — OpenRouteService Directions API
  - Retorna: ruta actual, distancia, tiempo estimado
- `get_alternative_route(origin: str, destination: str, avoid_polygon: list)` — ORS con zona de exclusion
  - `avoid_polygon`: lista de coordenadas `[[lon,lat],...]` definiendo el area de riesgo
  - Usa el parametro `options.avoid_polygons` de ORS Directions API
  - Retorna: ruta alternativa evitando la zona afectada
- `send_alert(message: str, severity: str)` — imprime alerta estructurada (simula notificacion)
- `confirm_action(action: str)` — registra decision tomada, retorna "Ejecucion OK"

**Output:** Plan de accion concreto con rutas alternativas + confirmacion de ejecucion.

---

## Orchestrator

Ejecuta los agentes en secuencia, pasando outputs como contexto:

```python
class Orchestrator:
    def run(self, scenario: str) -> FinalReport:
        risk_report     = self.risk_monitor.run(scenario)
        inventory_report = self.inventory_manager.run(risk_report.content)
        action_plan     = self.route_optimizer.run(
                            risk_report.content + "\n" + inventory_report.content
                          )
        return FinalReport(risk_report, inventory_report, action_plan)
```

---

## Escenario Demo

```
"Huracan categoria 4 detectado acercandose al Golfo de Mexico.
Evalua el impacto en nuestra cadena de suministro con centros
de distribucion en Veracruz, Houston y Tampa."
```

**Flujo esperado:**
1. RiskMonitor busca clima real de Veracruz/Houston/Tampa + noticias de huracan → reporta CRITICAL
2. InventoryManager evalua mock: identifica rutas maritimas Veracruz-Houston en riesgo, $2M en inventario afectado
3. RouteOptimizer calcula ruta alternativa real via ORS evitando el Golfo → emite alerta + confirma "Ejecucion OK"

---

## Stack y Dependencias

```toml
[dependencies]
groq = ">=0.9"           # LLM client (Groq API)
httpx = ">=0.27"         # HTTP para APIs externas
feedparser = ">=6.0"     # Parsear RSS feeds de noticias
python-dotenv = ">=1.0"  # Variables de entorno
```

**Variables de entorno (.env):**
```
GROQ_API_KEY=       # https://console.groq.com (free tier)
OWM_API_KEY=        # https://openweathermap.org/api (free tier)
ORS_API_KEY=        # https://openrouteservice.org (free tier, requiere registro)
```

---

## Estructura de Archivos

```
AgenticAi/
├── src/
│   ├── core/
│   │   ├── agent.py              # Clase Agent + loop agentivo
│   │   └── tool.py               # Clase Tool + dataclasses
│   ├── agents/
│   │   ├── risk_monitor.py       # Agent 1: instancia con tools reales
│   │   ├── inventory_manager.py  # Agent 2: instancia con tools mock
│   │   └── route_optimizer.py    # Agent 3: instancia con ORS tools
│   ├── tools/
│   │   ├── weather.py            # OpenWeatherMap integration
│   │   ├── news.py               # RSS feed parser
│   │   ├── inventory_mock.py     # Mock data + funciones
│   │   └── routing.py            # OpenRouteService integration
│   └── orchestrator.py           # Flujo Agent1 → Agent2 → Agent3
├── main.py                       # Punto de entrada + escenario demo
├── pyproject.toml
└── .env.example
```

---

## Verificacion

```bash
# 1. Instalar dependencias
pip install -e .

# 2. Copiar y completar .env
cp .env.example .env

# 3. Ejecutar demo
python main.py

# Output esperado:
# [RiskMonitor] Analizando escenario...
# [RiskMonitor] CRITICAL: Huracan Cat4 detectado, Veracruz/Tampa en zona de impacto
# [InventoryManager] Evaluando inventario afectado...
# [InventoryManager] Rutas maritimas VER-HOU comprometidas, $2M en riesgo
# [RouteOptimizer] Calculando rutas alternativas...
# [RouteOptimizer] Ruta alternativa confirmada via tierra HOU-MXC. Ejecucion OK
```
