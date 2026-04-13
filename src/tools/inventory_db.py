import json
import os
import time

from src.core.tool import Tool
from src.tools import inventory_mock  # fallback

_USE_POSTGRES: bool = False
_conn = None   # psycopg2 connection, managed by init_db()


def init_db() -> None:
    """Try to connect to Postgres and create tables. Falls back to mock silently."""
    global _USE_POSTGRES, _conn

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[DB] DATABASE_URL not set — using in-memory mock")
        return

    try:
        import psycopg2
    except ImportError:
        print("[DB] psycopg2 not installed — using in-memory mock")
        return

    for attempt in range(3):
        try:
            _conn = psycopg2.connect(db_url)
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"[DB] Cannot connect to Postgres ({e}) — using in-memory mock")
                return

    try:
        # Create tables (idempotent)
        with _conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS distribution_centers (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE,
                    name TEXT,
                    location TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    center_id INT REFERENCES distribution_centers(id),
                    name TEXT,
                    category TEXT,
                    stock_units INT,
                    value_usd INT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    origin TEXT,
                    destination TEXT,
                    carrier TEXT,
                    eta_days INT,
                    cargo_value_usd INT,
                    status TEXT
                )
            """)
            _conn.commit()

        # Seed from inventory_mock data (idempotent via ON CONFLICT DO NOTHING)
        with _conn.cursor() as cur:
            for key, data in inventory_mock.INVENTORY.items():
                cur.execute(
                    "INSERT INTO distribution_centers (key, name, location) VALUES (%s, %s, %s) ON CONFLICT (key) DO NOTHING",
                    (key, data["center"], data["location"]),
                )
                cur.execute("SELECT id FROM distribution_centers WHERE key = %s", (key,))
                row = cur.fetchone()
                if row is None:
                    continue
                center_id = row[0]
                for p in data["products"]:
                    cur.execute(
                        "INSERT INTO products (center_id, name, category, stock_units, value_usd) "
                        "SELECT %s, %s, %s, %s, %s WHERE NOT EXISTS "
                        "(SELECT 1 FROM products WHERE center_id = %s AND name = %s)",
                        (center_id, p["name"], p["category"], p["stock_units"], p["value_usd"],
                         center_id, p["name"]),
                    )
            for r in inventory_mock.ROUTES:
                cur.execute(
                    "INSERT INTO routes (id, type, origin, destination, carrier, eta_days, cargo_value_usd, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (r["id"], r["type"], r["origin"], r["destination"],
                     r["carrier"], r["eta_days"], r["cargo_value_usd"], r["status"]),
                )
            _conn.commit()
    except Exception as e:
        print(f"[DB] Setup failed ({e}) — using in-memory mock")
        _conn.close()
        _conn = None
        return

    _USE_POSTGRES = True
    print("[DB] Postgres ready — inventory backed by Postgres")


def get_inventory(location: str) -> str:
    global _USE_POSTGRES, _conn

    if not _USE_POSTGRES:
        return inventory_mock.get_inventory(location)

    key = location.lower().strip()
    try:
        with _conn.cursor() as cur:
            # fuzzy match: key contains location
            cur.execute(
                "SELECT dc.name, dc.location, dc.key, p.name, p.category, p.stock_units, p.value_usd "
                "FROM distribution_centers dc JOIN products p ON p.center_id = dc.id "
                "WHERE dc.key ILIKE %s",
                (f"%{key}%",),
            )
            rows = cur.fetchall()
    except Exception as e:
        _USE_POSTGRES = False
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
        return json.dumps({"error": f"DB query failed: {e}"})

    if not rows:
        return json.dumps({"error": f"Location '{location}' not found. Available: veracruz, houston, tampa"})

    dc_name = rows[0][0]
    dc_location = rows[0][1]
    products = [
        {"name": r[3], "category": r[4], "stock_units": r[5], "value_usd": r[6]}
        for r in rows
    ]
    return json.dumps({
        "center": dc_name,
        "location": dc_location,
        "products": products,
    }, ensure_ascii=False)


def get_active_routes() -> str:
    global _USE_POSTGRES, _conn

    if not _USE_POSTGRES:
        return inventory_mock.get_active_routes()

    try:
        with _conn.cursor() as cur:
            cur.execute(
                "SELECT id, type, origin, destination, carrier, eta_days, cargo_value_usd, status "
                "FROM routes WHERE status IN ('in_transit', 'scheduled')"
            )
            rows = cur.fetchall()
    except Exception as e:
        _USE_POSTGRES = False
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
        return json.dumps({"error": f"DB query failed: {e}"})

    routes = [
        {"id": r[0], "type": r[1], "origin": r[2], "destination": r[3],
         "carrier": r[4], "eta_days": r[5], "cargo_value_usd": r[6], "status": r[7]}
        for r in rows
    ]
    return json.dumps(routes, ensure_ascii=False)


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
