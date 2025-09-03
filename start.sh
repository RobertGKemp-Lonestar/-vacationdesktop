#!/bin/bash
set -e  # Exit on any error

# Railway start script for VacationDesktop
echo "🚀 Starting VacationDesktop deployment..."

# Debug environment
echo "PORT: $PORT"
echo "SECRET_KEY set: $([ -n "$SECRET_KEY" ] && echo "YES" || echo "NO")"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo "YES" || echo "NO")"
echo "DATABASE_URL (first 50 chars): ${DATABASE_URL:0:50}..."

# Fix DATABASE_URL if it contains railway.internal
if [[ "$DATABASE_URL" == *"railway.internal"* ]]; then
    echo "⚠️ Fixing DATABASE_URL with railway.internal hostname"
    # Extract connection details and use public hostname
    # This is a temporary fix - you should get the proper PUBLIC_URL from Railway
    export DATABASE_URL=$(echo $DATABASE_URL | sed 's/railway\.internal/roundhouse.proxy.rlwy.net/')
    echo "🔧 Updated DATABASE_URL (first 50 chars): ${DATABASE_URL:0:50}..."
fi

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

# Wait for database with Django's connection handling
echo "🔄 Waiting for database to be ready with Django..."
for i in {1..30}; do
    if python manage.py check --database default; then
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