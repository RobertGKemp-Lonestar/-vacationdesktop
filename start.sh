#!/bin/bash
set -e  # Exit on any error

# Railway start script for VacationDesktop
echo "🚀 Starting VacationDesktop deployment..."

# Debug environment
echo "PORT: $PORT"
echo "SECRET_KEY set: $([ -n "$SECRET_KEY" ] && echo "YES" || echo "NO")"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo "YES" || echo "NO")"
echo "DATABASE_URL (first 50 chars): ${DATABASE_URL:0:50}..."

# Check for required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is not set"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "⚠️ WARNING: PORT not set, using default 8000"
    export PORT=8000
fi

# Wait for database to be ready (with retries)
echo "🔄 Waiting for database to be ready..."
for i in {1..30}; do
    if python -c "
import os
import psycopg2
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
try:
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        database=url.path.lstrip('/')
    )
    conn.close()
    print('Database connection successful!')
    exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
"; then
        echo "✅ Database is ready!"
        break
    else
        echo "⏳ Database not ready, waiting... (attempt $i/30)"
        sleep 2
    fi
done

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "🌐 Starting Gunicorn server on port $PORT..."
exec gunicorn vacationdesktop.wsgi \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -