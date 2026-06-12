# ── AI绘图工作台 后端 Dockerfile ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy site-packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py config.py models.py utils.py ingest.py ./
COPY knowledge_db.py json_store.py seed_data.py embedding_service.py embedding_worker.py ./
COPY routers/ ./routers/
COPY providers/ ./providers/
COPY data/ ./data/

# Create volume mount for persisting SQLite DB
VOLUME /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
