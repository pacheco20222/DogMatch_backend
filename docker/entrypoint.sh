#!/bin/bash
# ============================================================================
# DogMatch Backend - Docker Entrypoint Script
# ============================================================================
# Purpose: Orchestrate container startup sequence
# - Wait for dependencies (MySQL, Redis)
# - Run database migrations
# - Create initial admin user
# - Start the application server
# ============================================================================

# Exit immediately if any command fails
# This ensures we don't start the app if migrations fail, for example
set -e

# Color codes for pretty output (optional but nice!)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function for logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# FUNCTION: Wait for MySQL Database
# ============================================================================
# Why? Docker Compose might start our app before MySQL is fully ready
# We need to wait until MySQL accepts connections before running migrations
wait_for_database() {
    log_info "Waiting for database to be ready..."
    
    # Extract database connection details from DATABASE_URL or individual vars
    # DATABASE_URL format: mysql+pymysql://user:pass@host:port/dbname
    if [ -n "$DATABASE_URL" ]; then
        # Parse DATABASE_URL
        DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+).*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.*/\1/')
        DB_USER=$(echo $DATABASE_URL | sed -E 's/.*:\/\/([^:]+).*/\1/')
        DB_PASSWORD=$(echo $DATABASE_URL | sed -E 's/.*:\/\/[^:]+:([^@]+).*/\1/')
        DB_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/([^?]+).*/\1/')
    else
        # Use individual environment variables (fallback)
        DB_HOST=${DB_HOST:-localhost}
        DB_PORT=${DB_PORT:-3306}
        DB_USER=${DB_USER:-root}
        DB_PASSWORD=${DB_PASSWORD}
        DB_NAME=${DB_NAME:-dogmatch}
    fi
    
    # Try to connect to MySQL (max 40 attempts = 120 seconds)
    # MySQL needs extra time on first startup to create database and users
    MAX_ATTEMPTS=40
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        # Try to connect using Python (works on systems without mysql client)
        # TEMPORARY: Show error on first few attempts for debugging
        if [ $ATTEMPT -eq 0 ]; then
            log_info "DEBUG: Trying to connect to MySQL with:"
            log_info "  Host: $DB_HOST"
            log_info "  Port: $DB_PORT"
            log_info "  User: $DB_USER"
            log_info "  Database: $DB_NAME"
            log_info "  Password: ${DB_PASSWORD:0:3}... (hidden)"
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        
        # Try connection and show errors on first 3 attempts
        if [ $ATTEMPT -le 3 ]; then
            python3 -c "
import sys
try:
    import pymysql
    connection = pymysql.connect(
        host='$DB_HOST',
        port=int('$DB_PORT'),
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME',
        connect_timeout=5
    )
    connection.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"
            if [ $? -eq 0 ]; then
                log_success "Database is ready!"
                return 0
            fi
        else
            # Silent attempts after first 3
            if python3 -c "
import sys
try:
    import pymysql
    connection = pymysql.connect(
        host='$DB_HOST',
        port=int('$DB_PORT'),
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME',
        connect_timeout=5
    )
    connection.close()
except:
    sys.exit(1)
" 2>/dev/null; then
                log_success "Database is ready!"
                return 0
            fi
        fi
        
        log_warning "Database not ready yet (attempt $ATTEMPT/$MAX_ATTEMPTS). Retrying in 3 seconds..."
        sleep 3
    done
    
    log_error "Database failed to become ready after $MAX_ATTEMPTS attempts"
    log_error "Check your DATABASE_URL and ensure MySQL is running"
    exit 1
}

# ============================================================================
# FUNCTION: Wait for Redis (Optional)
# ============================================================================
# Redis is used for caching and Socket.IO message queue
# It's optional in development but recommended in production
wait_for_redis() {
    # Only wait for Redis if it's configured
    if [ -z "$REDIS_URL" ]; then
        log_info "Redis not configured, skipping..."
        return 0
    fi
    
    log_info "Waiting for Redis to be ready..."
    
    # Extract Redis host and port from REDIS_URL
    # Format: redis://host:port/db or redis://:password@host:port/db
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's/redis:\/\/(:.*@)?([^:]+).*/\2/')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's/.*:([0-9]+)\/.*/\1/')
    
    MAX_ATTEMPTS=15
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        # Try to connect to Redis
        if python3 -c "
import sys
try:
    import redis
    r = redis.from_url('$REDIS_URL', socket_connect_timeout=5)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            log_success "Redis is ready!"
            return 0
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        log_warning "Redis not ready yet (attempt $ATTEMPT/$MAX_ATTEMPTS). Retrying in 2 seconds..."
        sleep 2
    done
    
    log_warning "Redis failed to become ready, continuing without it..."
    log_warning "Socket.IO will run in single-server mode"
    return 0  # Don't fail, just continue
}

# ============================================================================
# FUNCTION: Run Database Migrations
# ============================================================================
# Applies any pending database schema changes using Flask-Migrate
run_migrations() {
    log_info "Running database migrations..."
    
    # Check if migrations directory exists
    if [ ! -d "migrations" ]; then
        log_warning "Migrations directory not found. Initializing..."
        flask db init
    fi
    
    # Run migrations
    flask db upgrade
    
    if [ $? -eq 0 ]; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migrations failed!"
        exit 1
    fi
}

# ============================================================================
# FUNCTION: Create Admin User
# ============================================================================
# Creates the default admin user if it doesn't exist
# This is idempotent - safe to run multiple times
create_admin_user() {
    log_info "Checking admin user..."
    
    # Run the Flask CLI command to create admin
    # The command itself is idempotent (checks if admin exists first)
    flask create-admin
    
    if [ $? -eq 0 ]; then
        log_success "Admin user ready"
    else
        log_warning "Could not create admin user (might already exist)"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

log_info "======================================"
log_info "DogMatch Backend - Starting Up"
log_info "======================================"

# Print environment info (for debugging)
log_info "Environment: ${FLASK_ENV:-not set}"
log_info "Python version: $(python --version)"
log_info "Flask app: ${FLASK_APP:-not set}"

# Step 1: Wait for dependencies
log_info ""
log_info "Step 1: Checking dependencies..."
wait_for_database
wait_for_redis

# Step 2: Run migrations
log_info ""
log_info "Step 2: Running database migrations..."
run_migrations

# Step 3: Create admin user (only if in production or staging)
if [ "$FLASK_ENV" != "development" ] || [ "$CREATE_ADMIN" = "true" ]; then
    log_info ""
    log_info "Step 3: Setting up admin user..."
    create_admin_user
else
    log_info ""
    log_info "Step 3: Skipping admin creation (development mode)"
fi

# Step 4: Start the application
log_info ""
log_info "======================================"
log_success "Startup complete! Starting application..."
log_info "======================================"
log_info ""

# Execute the CMD from Dockerfile (Gunicorn)
# "$@" passes all arguments to this script (the CMD from Dockerfile)
exec "$@"