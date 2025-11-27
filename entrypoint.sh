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
# WAIT FOR DATABASE
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
        
        # Only use SSL for remote databases (Azure MySQL, AWS RDS, etc.)
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
# MAIN
# ======================================================
log_info "====================================="
log_info " DogMatch Backend - Starting Up "
log_info "====================================="
log_info "Environment: ${FLASK_ENV:-unset}"
log_info "Python version: $(python --version)"
log_info "Port: ${PORT:-8000}"

# Check dependencies
log_info "Checking dependencies..."
set +e
wait_for_database
DB_STATUS=$?
if [ $DB_STATUS -ne 0 ]; then
    log_warning "Database check failed, but continuing startup..."
fi
set -e

log_success "Dependencies OK!"

# Skip Nginx (not supported in Azure Web App for Containers)
log_info "Skipping Nginx (not supported in Azure Web App for Containers)"

# Start Gunicorn in the foreground (this will be the main process)
log_info "Starting Gunicorn on port ${PORT:-8000}..."
# Note: Running as root for Azure compatibility (Azure containers run as root by default)
# Gunicorn will bind to the PORT environment variable injected by Azure
exec gunicorn --config gunicorn.conf.py wsgi:app
