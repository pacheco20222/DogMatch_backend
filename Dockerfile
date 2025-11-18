# Stage 1: Builder
FROM python:3.12-slim as builder

LABEL maintainer="jrp2022@gmail.com"
LABEL description="Backend for DogMatch application, Builder Stage"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

LABEL maintainer="jrp2022@gmail.com"
LABEL description="Backend for DogMatch application, Runtime Stage"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH" \
    FLASK_APP=run.py

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non root user to run the application
# Use UID 1000 to avoid permission issues when mounting volumes
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash appuser

WORKDIR /app

COPY --from=builder /app/venv /app/venv

# Copy application code
COPY . .

RUN sed -i 's/\r$//' /app/docker/entrypoint.sh && \
    chmod +x /app/docker/entrypoint.sh

# Create logs directory only (photos are stored in S3, not locally)
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/api/health/live || exit 1

ENTRYPOINT [ "/app/docker/entrypoint.sh" ]

# Use wsgi.py as entry point instead of run.py
CMD ["gunicorn", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--workers", "1", "--bind", "0.0.0.0:5002", "--timeout", "120", "--log-level", "info", "wsgi:app"]
