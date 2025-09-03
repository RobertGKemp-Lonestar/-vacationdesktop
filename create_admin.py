#!/usr/bin/env python
"""
One-time script to create admin user for production deployment.
Run this once, then delete it.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacationdesktop.settings')
django.setup()

from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

# Create superuser if it doesn't exist
username = 'admin'
email = 'admin@example.com'
password = 'VacationAdmin2024!'  # Strong password

if not User.objects.filter(username=username).exists():
    # Get Super Admin role
    try:
        super_admin_role = Role.objects.get(name='Super Admin')
    except Role.DoesNotExist:
        print("❌ Super Admin role not found. Make sure to run 'python manage.py setup_rbac' first.")
        exit(1)
    
    # Create the user
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role=super_admin_role,
        first_name='System',
        last_name='Administrator'
    )
    
    print(f"✅ Superuser '{username}' created successfully!")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print("🚨 IMPORTANT: Change this password immediately after first login!")
else:
    print(f"ℹ️ User '{username}' already exists.")