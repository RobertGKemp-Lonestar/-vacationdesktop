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

# Create media directories with proper permissions
echo "📁 Creating media directories..."
mkdir -p media/tenant_logos
chmod 755 media
chmod 755 media/tenant_logos

# Test write permissions
if touch media/tenant_logos/.test_write 2>/dev/null; then
    rm -f media/tenant_logos/.test_write
    echo "✅ Media directories created with proper write permissions"
else
    echo "⚠️ WARNING: Media directory may not be writable"
fi

# Debug media configuration
echo "🔍 Running media configuration debug..."
python manage.py debug_media

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

# Create cache table if using database cache (Railway fallback)
echo "🗄️ Creating cache table if needed..."
python manage.py createcachetable || echo "Cache table may already exist or not needed"

# Setup RBAC system
echo "🔐 Setting up RBAC system..."
python manage.py setup_rbac

# Create admin user with management command
echo "👤 Creating admin user NOW..."
python manage.py create_admin_now

# Fix admin user role to be SUPER_ADMIN
echo "🔧 Fixing admin user role..."
python manage.py fix_admin_role

# Fix admin user tenant assignment
echo "🏢 Fixing admin user tenant assignment..."
python manage.py fix_admin_tenant

# Force fix RBAC permissions to ensure SUPER_ADMIN has all permissions
echo "🔐 Force fixing RBAC permissions..."
python manage.py force_fix_rbac

# Debug RBAC system
echo "🐞 RBAC Debug Report..."
python manage.py debug_rbac

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "🌐 Starting Gunicorn server on port $PORT..."
exec gunicorn vacationdesktop.wsgi \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --timeout 300 \
    --graceful-timeout 60 \
    --keep-alive 2 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --worker-connections 1000 \
    --access-logfile - \
    --error-logfile -