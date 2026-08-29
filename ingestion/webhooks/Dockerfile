FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn duckdb pandas

COPY ingestion/ ingestion/
COPY config/ config/

EXPOSE 8080

CMD ["uvicorn", "ingestion.webhooks.server:app", "--host", "0.0.0.0", "--port", "8080"]
