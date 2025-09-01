#!/bin/bash
set -e  # Exit on any error

# Railway start script for VacationDesktop
echo "🚀 Starting VacationDesktop deployment..."

# Check for required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is not set"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

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