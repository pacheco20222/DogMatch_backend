"""
Gunicorn configuration for DogMatch Backend
Production-ready settings for Azure Web App for Containers
"""

import os
import multiprocessing

# Server socket - Use PORT environment variable from Azure (defaults to 8000)
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = 4
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
worker_connections = 1000
threads = 2
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

# Process naming
proc_name = "dogmatch-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (not used in Azure, handled by Azure)
keyfile = None
certfile = None

# Performance tuning
max_requests = 1000
max_requests_jitter = 50
preload_app = False

# Graceful timeout
graceful_timeout = 30

# Worker timeout
worker_tmp_dir = "/dev/shm"

# StatsD (optional, for monitoring)
statsd_host = None
statsd_prefix = "gunicorn"

def when_ready(server):
    """Called just after the server is started."""
    port = os.getenv('PORT', '8000')
    server.log.info(f"Gunicorn server is ready on port {port}. Spawning workers.")

def worker_int(worker):
    """Called just after a worker has been killed."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker times out."""
    worker.log.warning("Worker timeout (pid: %s)", worker.pid)
