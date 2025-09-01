#!/bin/bash

# Railway start script for VacationDesktop
echo "Starting VacationDesktop deployment..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn vacationdesktop.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 30