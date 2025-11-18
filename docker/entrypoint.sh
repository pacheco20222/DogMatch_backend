#!/bin/bash
set -e

# ======================================================
# COLORS
# ======================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ======================================================
# WAIT FOR MYSQL  (WITH SSL ENABLED)
# ======================================================
wait_for_database() {
    if [ -z "$DATABASE_URL" ]; then
        log_warning "DATABASE_URL not set. Skipping DB wait."
        return 0
    fi

    log_info "Waiting for MySQL database to be ready..."

python3 - <<EOF
import sys
import time
import pymysql
from urllib.parse import urlparse

url = urlparse("${DATABASE_URL}")
host = url.hostname
port = url.port or 3306
user = url.username
password = url.password
db = url.path.lstrip("/")

for attempt in range(15):
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db,
            connect_timeout=4,
            ssl={
                "ca": "/etc/ssl/certs/ca-certificates.crt",
                "check_hostname" : False,
                "verify_mode": 0
            }   # <<<<< IMPORTANT FIX — ENABLE TLS
        )
        conn.close()
        print("[SUCCESS] Database is ready!")
        sys.exit(0)
    except Exception as e:
        print(f"[WARNING] Database not ready yet ({attempt+1}/15): {e}")
        time.sleep(2)

print("[ERROR] Database failed to respond in time.")
sys.exit(1)
EOF
}

# ======================================================
# WAIT FOR REDIS
# ======================================================
wait_for_redis() {
    if [ -z "$REDIS_URL" ]; then
        log_warning "REDIS_URL not set. Skipping Redis wait."
        return 0
    fi

    log_info "Waiting for Redis to be ready..."

python3 - <<EOF
import sys
import time
import redis

for attempt in range(10):
    try:
        r = redis.from_url("${REDIS_URL}", socket_connect_timeout=3)
        r.ping()
        print("[SUCCESS] Redis is ready!")
        sys.exit(0)
    except Exception as e:
        print(f"[WARNING] Redis not ready ({attempt+1}/10): {e}")
        time.sleep(2)

print("[WARNING] Redis did not respond, continuing anyway.")
sys.exit(0)
EOF
}

# ======================================================
# MAIN
# ======================================================
log_info "====================================="
log_info " DogMatch Backend - Starting Up "
log_info "====================================="
log_info "Environment: ${FLASK_ENV:-unset}"
log_info "Python version: $(python --version)"

log_info "Checking dependencies..."
wait_for_database
wait_for_redis

log_success "Dependencies OK! Starting Gunicorn..."

exec "$@"
