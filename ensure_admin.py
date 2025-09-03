#!/usr/bin/env python
import os
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacationdesktop.settings')
django.setup()

from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

def create_admin_user():
    username = 'admin'
    password = 'VacationAdmin2024!'
    email = 'admin@example.com'
    
    try:
        # Create or update admin user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            print(f"✅ Created new admin user: {username}")
        else:
            print(f"ℹ️ Admin user {username} already exists, updating password...")
            
        # Set password and role
        user.set_password(password)
        
        # Get Super Admin role
        try:
            super_admin_role = Role.objects.get(name='Super Admin')
            user.role = super_admin_role
        except Role.DoesNotExist:
            print("⚠️ Super Admin role not found, user will still have superuser permissions")
            
        user.save()
        
        print("🎯 ADMIN LOGIN CREDENTIALS:")
        print(f"   URL: https://web-production-c5d67.up.railway.app/login/")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

if __name__ == '__main__':
    success = create_admin_user()
    exit(0 if success else 1)