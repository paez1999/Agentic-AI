# Graph Report - .  (2026-04-14)

## Corpus Check
- Corpus is ~17,018 words - fits in a single context window. You may not need a graph.

## Summary
- 307 nodes · 399 edges · 49 communities detected
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 96 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_API Models and Scanner|API Models and Scanner]]
- [[_COMMUNITY_Architecture and Integration Protocols|Architecture and Integration Protocols]]
- [[_COMMUNITY_Agent Agentic Loop Core|Agent Agentic Loop Core]]
- [[_COMMUNITY_Inventory DB and MCP Loader|Inventory DB and MCP Loader]]
- [[_COMMUNITY_FastAPI Backend Routes|FastAPI Backend Routes]]
- [[_COMMUNITY_NATS Event Bus|NATS Event Bus]]
- [[_COMMUNITY_Analysis Job Store|Analysis Job Store]]
- [[_COMMUNITY_Port Registry|Port Registry]]
- [[_COMMUNITY_Routing MCP Server|Routing MCP Server]]
- [[_COMMUNITY_PostgreSQL Inventory Data|PostgreSQL Inventory Data]]
- [[_COMMUNITY_WebSocket Frontend Client|WebSocket Frontend Client]]
- [[_COMMUNITY_Inventory MCP Server|Inventory MCP Server]]
- [[_COMMUNITY_Routing Tools|Routing Tools]]
- [[_COMMUNITY_Report and Scan UI|Report and Scan UI]]
- [[_COMMUNITY_Simulation Dialog UI|Simulation Dialog UI]]
- [[_COMMUNITY_News MCP Server|News MCP Server]]
- [[_COMMUNITY_Weather MCP Server|Weather MCP Server]]
- [[_COMMUNITY_Main Entry Point|Main Entry Point]]
- [[_COMMUNITY_Auto Scan Controls|Auto Scan Controls]]
- [[_COMMUNITY_Port Store State|Port Store State]]
- [[_COMMUNITY_Inventory Mock Data|Inventory Mock Data]]
- [[_COMMUNITY_Map Generator|Map Generator]]
- [[_COMMUNITY_Next.js Root Layout|Next.js Root Layout]]
- [[_COMMUNITY_Add Port Dialog|Add Port Dialog]]
- [[_COMMUNITY_Alert Panel|Alert Panel]]
- [[_COMMUNITY_Risk Badge|Risk Badge]]
- [[_COMMUNITY_Status Bar|Status Bar]]
- [[_COMMUNITY_TypeScript API Client|TypeScript API Client]]
- [[_COMMUNITY_Weather Tool|Weather Tool]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Next.js Types|Next.js Types]]
- [[_COMMUNITY_Next.js Config|Next.js Config]]
- [[_COMMUNITY_PostCSS Config|PostCSS Config]]
- [[_COMMUNITY_Tailwind Config|Tailwind Config]]
- [[_COMMUNITY_Main Page|Main Page]]
- [[_COMMUNITY_Metrics Bar|Metrics Bar]]
- [[_COMMUNITY_Port Card|Port Card]]
- [[_COMMUNITY_Port Grid|Port Grid]]
- [[_COMMUNITY_Simulation Panel|Simulation Panel]]
- [[_COMMUNITY_Event Icons|Event Icons]]
- [[_COMMUNITY_Frontend Types|Frontend Types]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_CloudEvents Envelope|CloudEvents Envelope]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Vector DB Memory|Vector DB Memory]]
- [[_COMMUNITY_WebSocket Real-time UI|WebSocket Real-time UI]]

## God Nodes (most connected - your core abstractions)
1. `RiskLevel` - 18 edges
2. `PortRegistry` - 16 edges
3. `SimulationStore` - 16 edges
4. `Tool` - 16 edges
5. `Supply Chain PoC Multi-Agent System` - 15 edges
6. `AnalysisJobStore` - 13 edges
7. `AddPortBody` - 12 edges
8. `AutoScanBody` - 12 edges
9. `CreateSimulationBody` - 12 edges
10. `PortStatus` - 12 edges

## Surprising Connections (you probably didn't know these)
- `forced_tool_calls: if provided, these tool calls are executed upfront before` --uses--> `Tool`  [INFERRED]
  src\core\agent.py → src\core\tool.py
- `Run forced_tool_calls upfront. Returns (assistant_msgs, tool_result_msgs).` --uses--> `Tool`  [INFERRED]
  src\core\agent.py → src\core\tool.py
- `Entry point that runs the supply-chain pipeline using MCP servers.  Each tool (w` --uses--> `MCPServerConnection`  [INFERRED]
  main_mcp.py → src\core\mcp_loader.py
- `Entry point that runs the supply-chain pipeline using MCP servers.  Each tool (w` --uses--> `Orchestrator`  [INFERRED]
  main_mcp.py → src\orchestrator.py
- `AnalysisJobStore` --uses--> `FullAnalysisJob`  [INFERRED]
  backend\analysis_jobs.py → backend\models.py

## Hyperedges (group relationships)
- **Multi-Agent Sequential Pipeline** — claude_md_riskmonitor, claude_md_inventory_manager, claude_md_route_optimizer, spec_orchestrator [EXTRACTED 1.00]
- **External Tool Integrations** — plan_md_openweathermap, plan_md_ors_api, plan_md_bbc_rss, plan_md_gdacs_rss, plan_md_nhc_rss, plan_md_reuters_rss [EXTRACTED 1.00]
- **Data Persistence Layer** — claude_md_postgresql, claude_md_redis, plan_md_inventory_db, plan_md_psycopg2 [INFERRED 0.85]
- **Integration Protocol Stack** — claude_md_mcp, claude_md_a2a, claude_md_cloudevents, claude_md_nats, claude_md_rest_gateway, claude_md_oauth2_jwt [EXTRACTED 1.00]

## Communities

### Community 0 - "API Models and Scanner"
Cohesion: 0.09
Nodes (24): AddPortBody, AutoScanBody, CreateSimulationBody, Scan every monitored port and broadcast results., BaseModel, Enum, AutoScanConfig, FullAnalysisJob (+16 more)

### Community 1 - "Architecture and Integration Protocols"
Cohesion: 0.08
Nodes (36): Agent-to-Agent A2A Protocol, CloudEvents over NATS, CrewAI Framework, InventoryManager Agent, LangGraph, MCP Model Context Protocol, NATS Event Bus, OAuth2 JWT Security (+28 more)

### Community 2 - "Agent Agentic Loop Core"
Cohesion: 0.08
Nodes (19): Agent, AgentResult, forced_tool_calls: if provided, these tool calls are executed upfront before, Run forced_tool_calls upfront. Returns (assistant_msgs, tool_result_msgs)., create_inventory_manager_mcp(), Same as create_inventory_manager() but tools come from MCP servers.      tools —, _extract_route_geometries(), create_orchestrator_for_port() (+11 more)

### Community 3 - "Inventory DB and MCP Loader"
Cohesion: 0.1
Nodes (13): init_db(), Try to connect to Postgres and create tables. Falls back to mock silently., MCPServerConnection, Sync-friendly MCP client loader.  Wraps the async MCP client in a background dae, Shut down the MCP session and server subprocess., Maintains a persistent connection to one MCP server subprocess.      The MCP cli, Submit a coroutine to the background loop and block until done., Return MCP tool descriptors from the server. (+5 more)

### Community 4 - "FastAPI Backend Routes"
Cohesion: 0.14
Nodes (9): add_port(), clear_simulations(), create_simulation(), list_ports(), remove_simulation(), _scan_all(), scan_all_now(), scan_port_now() (+1 more)

### Community 5 - "NATS Event Bus"
Cohesion: 0.14
Nodes (9): EventBus, NATS event bus with CloudEvents envelope.  Publishes domain events from the supp, Subscribe to a NATS subject.          callback(subject, data) is called in the b, Sync-friendly NATS publisher + subscriber backed by a daemon asyncio thread., Publish a CloudEvent to a NATS subject (fire-and-forget, sync)., _wrap(), check_server(), main() (+1 more)

### Community 6 - "Analysis Job Store"
Cohesion: 0.18
Nodes (2): AnalysisJobStore, ConnectionManager

### Community 7 - "Port Registry"
Cohesion: 0.25
Nodes (1): PortRegistry

### Community 8 - "Routing MCP Server"
Cohesion: 0.2
Nodes (9): confirm_action(), get_alternative_route(), get_route(), MCP server exposing routing / TMS tools.  Run standalone:     python mcp_servers, Get the current route between two cities via OpenRouteService.      Returns JSON, Get an alternative route that avoids a geographic risk polygon.      avoid_polyg, Send a supply chain risk alert.      severity must be one of: LOW, MEDIUM, HIGH,, Record a decision and confirm its execution.      Returns a JSON object with sta (+1 more)

### Community 9 - "PostgreSQL Inventory Data"
Cohesion: 0.33
Nodes (7): PostgreSQL State and Audit, Feature 2: PostgreSQL Inventory, inventory_db.py, inventory_mock.py, psycopg2-binary PostgreSQL Driver, Hurricane Gulf of Mexico Demo Scenario, Distribution Centers: Veracruz, Houston, Tampa

### Community 10 - "WebSocket Frontend Client"
Cohesion: 0.33
Nodes (1): SupplyChainWS

### Community 11 - "Inventory MCP Server"
Cohesion: 0.33
Nodes (5): get_active_routes(), get_inventory(), MCP server exposing inventory / ERP tools.  Run standalone:     python mcp_serve, Get inventory levels at a distribution center.      Available locations: Veracru, Get all active supply chain routes.      Returns a JSON list of routes with id,

### Community 12 - "Routing Tools"
Cohesion: 0.47
Nodes (3): get_alternative_route(), get_route(), _resolve_coords()

### Community 13 - "Report and Scan UI"
Cohesion: 0.4
Nodes (0): 

### Community 14 - "Simulation Dialog UI"
Cohesion: 0.5
Nodes (0): 

### Community 15 - "News MCP Server"
Cohesion: 0.5
Nodes (3): get_news(), MCP server exposing the news / RSS aggregation tool.  Run standalone:     python, Search supply chain and weather news across multiple RSS feeds.      Fans out ac

### Community 16 - "Weather MCP Server"
Cohesion: 0.5
Nodes (3): get_weather(), MCP server exposing the weather tool.  Run standalone:     python mcp_servers/we, Get current weather conditions for a city.      Returns a JSON object with: temp

### Community 17 - "Main Entry Point"
Cohesion: 1.0
Nodes (2): check_server(), main()

### Community 18 - "Auto Scan Controls"
Cohesion: 0.67
Nodes (0): 

### Community 19 - "Port Store State"
Cohesion: 0.67
Nodes (0): 

### Community 20 - "Inventory Mock Data"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Map Generator"
Cohesion: 0.67
Nodes (2): generate_route_map(), Generate an HTML route map and return the absolute path.

### Community 22 - "Next.js Root Layout"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Add Port Dialog"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Alert Panel"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Risk Badge"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Status Bar"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "TypeScript API Client"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Weather Tool"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Next.js Types"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Next.js Config"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "PostCSS Config"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Tailwind Config"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Main Page"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Metrics Bar"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Port Card"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Port Grid"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Simulation Panel"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Event Icons"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Frontend Types"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "CloudEvents Envelope"
Cohesion: 1.0
Nodes (1): Wrap data in a CloudEvents 1.0 JSON envelope.

### Community 45 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Vector DB Memory"
Cohesion: 1.0
Nodes (1): Vector DB Semantic Memory

### Community 48 - "WebSocket Real-time UI"
Cohesion: 1.0
Nodes (1): WebSocket Real-time UI

## Knowledge Gaps
- **34 isolated node(s):** `MCP server exposing inventory / ERP tools.  Run standalone:     python mcp_serve`, `Get inventory levels at a distribution center.      Available locations: Veracru`, `Get all active supply chain routes.      Returns a JSON list of routes with id,`, `MCP server exposing the news / RSS aggregation tool.  Run standalone:     python`, `Search supply chain and weather news across multiple RSS feeds.      Fans out ac` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Next.js Root Layout`** (2 nodes): `layout.tsx`, `RootLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Add Port Dialog`** (2 nodes): `AddPortDialog()`, `AddPortDialog.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Alert Panel`** (2 nodes): `AlertPanel()`, `AlertPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Risk Badge`** (2 nodes): `RiskBadge.tsx`, `RiskBadge()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Status Bar`** (2 nodes): `StatusBar.tsx`, `StatusBar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TypeScript API Client`** (2 nodes): `request()`, `api.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Weather Tool`** (2 nodes): `weather.py`, `get_weather()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Next.js Types`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Next.js Config`** (1 nodes): `next.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PostCSS Config`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tailwind Config`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Main Page`** (1 nodes): `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Metrics Bar`** (1 nodes): `MetricsBar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Port Card`** (1 nodes): `PortCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Port Grid`** (1 nodes): `PortGrid.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Simulation Panel`** (1 nodes): `SimulationPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Event Icons`** (1 nodes): `eventIcons.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend Types`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `CloudEvents Envelope`** (1 nodes): `Wrap data in a CloudEvents 1.0 JSON envelope.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vector DB Memory`** (1 nodes): `Vector DB Semantic Memory`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WebSocket Real-time UI`** (1 nodes): `WebSocket Real-time UI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Tool` connect `Inventory DB and MCP Loader` to `Agent Agentic Loop Core`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `Entry point that runs the supply-chain pipeline using MCP servers.  Each tool (w` connect `NATS Event Bus` to `Agent Agentic Loop Core`, `Inventory DB and MCP Loader`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `MCPServerConnection` connect `Inventory DB and MCP Loader` to `NATS Event Bus`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `RiskLevel` (e.g. with `AddPortBody` and `AutoScanBody`) actually correct?**
  _`RiskLevel` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PortRegistry` (e.g. with `AddPortBody` and `AutoScanBody`) actually correct?**
  _`PortRegistry` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `SimulationStore` (e.g. with `AnalysisJobStore` and `AddPortBody`) actually correct?**
  _`SimulationStore` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Tool` (e.g. with `AgentResult` and `Agent`) actually correct?**
  _`Tool` has 14 INFERRED edges - model-reasoned connections that need verification._