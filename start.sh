#!/bin/bash
set -e  # Exit on any error

# Railway start script for VacationDesktop
echo "🚀 Starting VacationDesktop deployment..."

# Debug environment
echo "PORT: $PORT"
echo "SECRET_KEY set: $([ -n "$SECRET_KEY" ] && echo "YES" || echo "NO")"
echo "DATABASE_PUBLIC_URL set: $([ -n "$DATABASE_PUBLIC_URL" ] && echo "YES" || echo "NO")"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo "YES" || echo "NO")"
if [ -n "$DATABASE_PUBLIC_URL" ]; then
    echo "DATABASE_PUBLIC_URL (first 50 chars): ${DATABASE_PUBLIC_URL:0:50}..."
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

# Setup RBAC system
echo "🔐 Setting up RBAC system..."
python manage.py setup_rbac

# Create admin user using Django's built-in command
echo "👤 Creating admin user with Django command..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from rbac.models import Role
import traceback

try:
    User = get_user_model()
    
    # Delete existing admin if exists
    User.objects.filter(username='admin').delete()
    print('Deleted existing admin user')
    
    # Get Super Admin role
    role = Role.objects.get(name='Super Admin')
    print(f'Found role: {role.name}')
    
    # Create admin user
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com', 
        password='VacationAdmin2024!',
        first_name='System',
        last_name='Administrator'
    )
    user.role = role
    user.save()
    
    print('✅ SUCCESS: Admin user created!')
    print('Username: admin')
    print('Password: VacationAdmin2024!')
    print('Email: admin@example.com')
    
except Exception as e:
    print(f'❌ ERROR: {e}')
    traceback.print_exc()
"

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