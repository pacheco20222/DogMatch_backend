# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim as builder

LABEL maintainer="jrp2022@gmail.com"
LABEL description="DogMatch Backend - Builder Stage"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Final image with app and gunicorn only
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="jrp2022@gmail.com"
LABEL description="DogMatch Backend - Production Runtime (Azure Web App for Containers)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH" \
    PORT=8000

# Install runtime dependencies (mysql client, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy application code
COPY app /app/app
COPY migrations /app/migrations
COPY wsgi.py /app/
COPY requirements.txt /app/

# Copy configuration files
COPY gunicorn.conf.py /app/
COPY entrypoint.sh /app/

# Set permissions for entrypoint
RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Expose port (Azure will inject PORT environment variable)
EXPOSE 8000

# Health check (Azure will inject PORT, default to 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8000}/api/health/live || exit 1'

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (will be overridden by entrypoint)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
