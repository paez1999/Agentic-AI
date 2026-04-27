FROM python:3.11-slim

WORKDIR /app

# Install dependencies (excluding mlx-lm — Apple Silicon only)
RUN pip install --no-cache-dir \
    "openai>=1.0" \
    "httpx>=0.27" \
    "feedparser>=6.0" \
    "python-dotenv>=1.0" \
    "psycopg2-binary>=2.9" \
    "folium>=0.18" \
    "fastapi>=0.111" \
    "uvicorn[standard]>=0.29" \
    "pydantic>=2.0" \
    "websockets>=12.0" \
    "mcp[cli]>=1.0" \
    "nats-py>=2.0" \
    "cloudevents>=1.0" \
    "searoute>=1.5"

COPY . .

# Remove stale pyc cache from host
RUN find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find . -name "*.pyc" -delete 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
