#!/usr/bin/env python
"""
Reset admin user script - creates or updates admin user
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacationdesktop.settings')
django.setup()

from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'VacationAdmin2024!'

try:
    # Get or create Super Admin role
    super_admin_role, created = Role.objects.get_or_create(
        name='Super Admin',
        defaults={
            'description': 'Full system access across all tenants',
            'level': 1
        }
    )
    
    # Delete existing admin user if it exists
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
        print(f"🗑️ Deleted existing user '{username}'")
    
    # Create new admin user
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        first_name='System',
        last_name='Administrator'
    )
    user.role = super_admin_role
    user.save()
    
    print(f"✅ Admin user created successfully!")
    print(f"👤 Username: {username}")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print(f"🚀 Login at: https://web-production-c5d67.up.railway.app/login/")
    
except Exception as e:
    print(f"❌ Error creating admin user: {e}")
    import traceback
    traceback.print_exc()