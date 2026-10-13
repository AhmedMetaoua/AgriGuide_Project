# Contexte de build = racine du repo (voir docker-compose.yml : `context: .`),
# pas ce dossier — nécessaire pour pouvoir COPY backend/shared, qui est en
# dehors de backend/orchestrator/. Tous les chemins COPY ci-dessous sont donc
# relatifs à la racine, pas à ce Dockerfile.
FROM python:3.12-slim

WORKDIR /app

COPY backend/shared /shared
RUN pip install --no-cache-dir /shared

COPY backend/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/orchestrator/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
