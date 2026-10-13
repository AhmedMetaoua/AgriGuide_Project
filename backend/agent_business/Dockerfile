# Contexte de build = racine du repo (voir docker-compose.yml : `context: .`).
# Chemins COPY relatifs à la racine, pas à ce Dockerfile — même remarque
# que backend/orchestrator/Dockerfile.
FROM python:3.12-slim

WORKDIR /app

COPY backend/shared /shared
RUN pip install --no-cache-dir /shared

COPY backend/agent_business/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/agent_business/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
