# PoC Multi-Agente de Supply Chain con CrewAI

PoC en Python para simular una optimizacion de cadena de suministro usando tres agentes:

- Monitor del Entorno
- Gestor de Inventario
- Optimizador de Rutas

## Requisitos

- Python 3.10+

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Opcional (si quieres experimentar con CrewAI en un entorno compatible):

```bash
pip install -r requirements.crewai.optional.txt
```

## Ejecucion

```bash
python main.py
```

## Ejecucion con Docker

1) Crear archivo `.env` desde plantilla:

```bash
cp .env.example .env
```

2) Build de imagen:

```bash
docker build -t supply-chain-poc .
```

3) Ejecutar contenedor:

```bash
docker run --rm --env-file .env supply-chain-poc
```

## Ejecucion con Docker Compose

```bash
docker compose up --build
```

### Frontend UI (Streamlit)

Levanta solo la interfaz:

```bash
docker compose up --build supply-chain-ui
```

Abre en tu navegador:

- http://localhost:8501

La UI incluye listas sugeridas de:

- puertos estratégicos globales,
- orígenes logísticos clave,
- destinos de distribución,
- productos estratégicos.

Esto mejora la probabilidad de encontrar noticias geopolíticas relevantes para el análisis.

Además, la UI tiene:

- **Modo básico (default):** `origen` se sincroniza automáticamente con el puerto importante.
- **Modo avanzado:** permite editar origen y destino manualmente.

## Donde conectar APIs reales

Para reemplazar mocks por servicios reales:

- `src/tools/mock_tools.py`
  - `check_weather_and_news`: integrar proveedor real de clima/noticias/logistica.
  - `check_erp_inventory`: integrar API ERP (SAP, Oracle, etc.).
  - `calculate_alternative_routes`: integrar motor de rutas/TMS/freight API.
- `src/tasks/definitions.py`
  - Ajustar prompts/objetivos si quieres delegar mas razonamiento al LLM.
- `src/config.py`
  - Agregar nuevas variables de entorno segun tus proveedores.

## Notas

- Esta PoC no usa APIs pagas por defecto y funciona totalmente offline con datos mock.
- Si luego quieres integrar un LLM real, agrega las variables en `.env` y reemplaza las secciones marcadas en `src/tools/mock_tools.py`.
- Flujo actual hibrido:
  - Agente 1: usa datos online reales (Open-Meteo + GDELT).
  - Agente 2: usa inventario estatico local.
  - Agente 3: ajusta opciones usando los hallazgos online del Agente 1.
