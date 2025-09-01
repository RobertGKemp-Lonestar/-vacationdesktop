#!/bin/bash
# Production-like server startup script

echo "Starting VacationDesktop in production mode..."

# Activate virtual environment
source venv/bin/activate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start Gunicorn server
echo "Starting Gunicorn server..."
gunicorn -c gunicorn.conf.py vacationdesktop.wsgi:application