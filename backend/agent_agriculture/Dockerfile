# Contexte de build = racine du repo (voir docker-compose.yml : `context: .`).
# Chemins COPY relatifs à la racine, pas à ce Dockerfile — même remarque
# que backend/orchestrator/Dockerfile et backend/agent_business/Dockerfile.
FROM python:3.12-slim

WORKDIR /app

# libgomp1: required by torch's CPU backend at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/shared /shared
RUN pip install --no-cache-dir /shared

COPY backend/agent_agriculture/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/agent_agriculture/app ./app
COPY backend/agent_agriculture/scripts ./scripts

# Persisted via docker-compose volumes (see docker-compose.yml) so the RAG
# corpus and the fine-tuned DL checkpoint survive container restarts.
RUN mkdir -p /app/chroma_store /app/dl_checkpoints

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
