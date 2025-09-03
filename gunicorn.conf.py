# Gunicorn configuration file for production-like development

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - Use stdout/stderr for Railway deployment
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# Process naming
proc_name = "vacationdesktop"

# Daemon mode
daemon = False
# pidfile = "logs/gunicorn.pid"  # Disabled for Railway - no persistent storage

# User and group to run as (for production)
# user = "www-data"
# group = "www-data"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (for production with certificates)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=vacationdesktop.settings',
]