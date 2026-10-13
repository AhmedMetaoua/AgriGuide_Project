FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# streamlit is only used by interface_test/ (local dev UI) — not needed in the API image.
COPY requirements.txt .
RUN sed -i "/^streamlit/d" requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
