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

# Determine if we should use SSL
# Local Docker MySQL (hostname 'mysql') doesn't need SSL
use_ssl = host not in ['mysql', 'localhost', '127.0.0.1']

for attempt in range(15):
    try:
        connect_args = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': db,
            'connect_timeout': 4
        }
        
        # Only use SSL for remote databases (AWS RDS, etc.)
        if use_ssl:
            connect_args['ssl'] = {
                "ca": "/etc/ssl/certs/ca-certificates.crt",
                "check_hostname": False,
                "verify_mode": 0
            }
        
        conn = pymysql.connect(**connect_args)
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

    # For local development, Redis connection failures are non-fatal
    # The app will handle Redis connection gracefully
    log_info "Checking Redis connection (non-blocking for local dev)..."

python3 - <<EOF
import sys
import time
import redis
import ssl
from urllib.parse import urlparse

redis_url = "${REDIS_URL}"

# Parse URL to extract connection details
parsed = urlparse(redis_url)
is_ssl = parsed.scheme == 'rediss'

for attempt in range(10):
    try:
        # Extract connection details from URL
        host = parsed.hostname
        port = parsed.port or 6379
        password = parsed.password
        username = parsed.username or 'default'
        db = int(parsed.path.lstrip('/')) if parsed.path else 0
        
        # Create Redis connection with proper SSL configuration for Redis Labs
        if is_ssl:
            # Try using from_url first as it handles SSL automatically
            try:
                r = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    ssl_cert_reqs=None,  # Disable certificate verification
                    ssl_check_hostname=False
                )
            except Exception:
                # Fallback to manual configuration
                r = redis.Redis(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    db=db,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    ssl=True,
                    ssl_cert_reqs=None,  # Use None instead of ssl.CERT_NONE
                    ssl_ca_certs=None,
                    ssl_check_hostname=False
                )
        else:
            r = redis.Redis(
                host=host,
                port=port,
                username=username,
                password=password,
                db=db,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        
        r.ping()
        print(f"[SUCCESS] Redis is ready! (SSL: {is_ssl})")
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
# Temporarily disable exit on error for dependency checks
# Don't fail the container if database/redis aren't ready - let the app handle retries
set +e
wait_for_database
DB_STATUS=$?
if [ $DB_STATUS -ne 0 ]; then
    log_warning "Database check failed, but continuing startup..."
fi

wait_for_redis
REDIS_STATUS=$?
if [ $REDIS_STATUS -ne 0 ]; then
    log_warning "Redis check failed, but continuing startup..."
fi
set -e

log_success "Dependencies OK! Starting Gunicorn..."

exec "$@"
