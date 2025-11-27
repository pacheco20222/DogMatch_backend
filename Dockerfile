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
# Stage 2: Runtime - Final image with app, nginx, and gunicorn
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="jrp2022@gmail.com"
LABEL description="DogMatch Backend - Production Runtime"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH" \
    PORT=8000

# Install runtime dependencies (nginx, mysql client, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /etc/nginx/sites-enabled/default

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
COPY nginx.conf /app/
COPY entrypoint.sh /app/

# Set permissions for entrypoint
RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy nginx config to system location
RUN cp /app/nginx.conf /etc/nginx/nginx.conf && \
    mkdir -p /var/log/nginx /var/lib/nginx /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx /var/lib/nginx /var/cache/nginx

# Note: Container runs as root by default in Azure
# Nginx master process needs root to bind to port 80
# Gunicorn will run as appuser via entrypoint

# Expose port 8000 (Gunicorn) and 80 (Nginx)
EXPOSE 8000 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/api/health/live || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (will be overridden by entrypoint)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
