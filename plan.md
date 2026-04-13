# Implementation Plan

## Current State

| Agent | Tool | Status |
|---|---|---|
| RiskMonitor | `get_weather` → OpenWeatherMap API | Real |
| RiskMonitor | `get_news` → BBC RSS only | Real but narrow — rarely matches supply chain events |
| InventoryManager | `get_inventory` / `get_active_routes` | Hardcoded Python dicts in `inventory_mock.py` |
| RouteOptimizer | `get_route` / `get_alternative_route` → ORS API | Real (returns km/hours only) |
| RouteOptimizer | Map output | None — text only |

---

## Feature 1 — Agent 1: Multi-Source News + Visible Output

### Problem
BBC RSS is general world news; hurricane/supply-chain queries rarely match, causing the agent to fall back to unrelated headlines. The weather and news data found are also not displayed to the user in a readable format.

### Plan

**`src/tools/news.py`**
- Fan out across 4 RSS feeds instead of BBC only:
  - BBC World: `https://feeds.bbci.co.uk/news/world/rss.xml`
  - GDACS disaster alerts: `https://www.gdacs.org/xml/rss.xml`
  - National Hurricane Center: `https://www.nhc.noaa.gov/index-at.xml`
  - Reuters world: `https://feeds.reuters.com/reuters/worldNews`
- Parse all feeds in parallel, merge entries, filter by query terms, return top 5 matches
- No new dependencies — `feedparser` already handles all RSS formats

**`src/orchestrator.py`**
- After Phase 1 completes, print a formatted "LIVE DATA" block:
  - Weather table per city (temp, humidity, wind speed, condition)
  - News articles list with title + link

---

## Feature 2 — Agent 2: PostgreSQL Inventory

### Problem
`inventory_mock.py` has static hardcoded data. Agent 2 needs a real queryable database that can be updated independently of the code.

### Plan

**`docker-compose.yml`**
- Add a `postgres:16-alpine` service:
  - DB: `supply_chain`, user: `scuser`, password: `scpass`
  - Port: `5432`
  - Named volume for persistence

**`pyproject.toml`**
- Add dependency: `psycopg2-binary>=2.9`

**`src/tools/inventory_db.py`** (new file, replaces `inventory_mock.py`)
- `init_db()`: creates tables + seeds initial data using `CREATE TABLE IF NOT EXISTS` (idempotent, safe to call on every startup)
- `get_inventory(location)`: queries `distribution_centers JOIN products`
- `get_active_routes()`: queries `routes WHERE status IN ('in_transit', 'scheduled')`
- Returns same JSON format as the mock so agent prompt is unchanged

**DB schema:**
```sql
CREATE TABLE distribution_centers (id SERIAL PRIMARY KEY, name TEXT, location TEXT);
CREATE TABLE products (id SERIAL PRIMARY KEY, center_id INT REFERENCES distribution_centers, name TEXT, category TEXT, stock_units INT, value_usd INT);
CREATE TABLE routes (id TEXT PRIMARY KEY, type TEXT, origin TEXT, destination TEXT, carrier TEXT, eta_days INT, cargo_value_usd INT, status TEXT);
```
Seeded with the same data currently in `inventory_mock.py`.

**`src/agents/inventory_manager.py`**
- Change import from `inventory_mock` → `inventory_db`

**`.env` / `.env.example`**
- Add `DATABASE_URL=postgresql://scuser:scpass@localhost:5432/supply_chain`

**`main.py`**
- Call `init_db()` before running the orchestrator

---

## Feature 3 — Agent 3: Visual Route Maps

### Problem
RouteOptimizer returns distance/duration text only. No visual of original vs. alternative route, distribution center locations, or the hurricane risk zone.

### Plan

**`pyproject.toml`**
- Add: `folium>=0.18`, `polyline>=2.0`

**`src/tools/routing.py`**
- Modify `get_route` and `get_alternative_route`:
  - Add `"geometry": true` to the ORS request body to receive the encoded route polyline
  - Decode the polyline and include the coordinates in the returned JSON
  - The agent's text report is unaffected; geometry is extra data in the response

**`src/tools/map_generator.py`** (new file)
- `generate_route_map(original_geometry, alt_geometry, risk_polygon, output_path)`:
  - `folium.Map` centered on Gulf of Mexico (24°N, 90°W), zoom 5
  - Markers for Veracruz, Houston, Tampa with labels
  - Red polyline: original route
  - Green polyline: alternative route
  - Semi-transparent red polygon: hurricane risk zone
  - Saves to `output/route_map.html`, returns file path

**`src/orchestrator.py`**
- After Phase 3 completes, extract route geometries from the agent's tool response messages
- Call `generate_route_map(...)` with the collected geometries
- Print the output path and auto-open in browser with `webbrowser.open()`

**`output/`** directory
- Create it, add to `.gitignore`

---

## Files Touched

| File | Change |
|---|---|
| `pyproject.toml` | Add `psycopg2-binary`, `folium`, `polyline` |
| `docker-compose.yml` | Add `postgres` service + named volume |
| `.env` / `.env.example` | Add `DATABASE_URL` |
| `main.py` | Call `init_db()` at startup |
| `src/tools/news.py` | Multi-feed RSS fan-out |
| `src/tools/inventory_mock.py` | Kept for reference, no longer used |
| `src/tools/inventory_db.py` | New — psycopg2 queries replacing mock |
| `src/tools/routing.py` | Add geometry extraction to both route tools |
| `src/tools/map_generator.py` | New — folium map builder |
| `src/agents/inventory_manager.py` | Import from `inventory_db` instead of `inventory_mock` |
| `src/orchestrator.py` | Formatted Phase 1 live data output + map generation after Phase 3 |
| `output/.gitkeep` | New — output directory placeholder |

---

## Verification

```bash
# 1. Start the database
docker compose up -d postgres

# 2. Install new dependencies
pip install -e .

# 3. Run the pipeline
python main.py
```

Expected result:
- **Phase 1**: Formatted weather table + real news article titles with links printed to console
- **Phase 2**: Inventory read from Postgres (verifiable via `psql` or DB client)
- **Phase 3**: `output/route_map.html` opens in browser showing original route (red), alternative route (green), and hurricane risk zone (red polygon) with DC markers
