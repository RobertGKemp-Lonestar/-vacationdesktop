#!/usr/bin/env python
"""
Direct SQL approach to create admin user when Django isn't working
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacationdesktop.settings')
django.setup()

from django.db import connection
from django.contrib.auth.hashers import make_password
from datetime import datetime

def create_admin_sql():
    username = 'admin'
    email = 'admin@example.com' 
    password = 'VacationAdmin2024!'
    
    # Hash the password using Django's method
    hashed_password = make_password(password)
    
    with connection.cursor() as cursor:
        try:
            # Check if user table exists
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE '%user%';
            """)
            tables = cursor.fetchall()
            print("User-related tables:", tables)
            
            # Try to find the correct user table
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            all_tables = cursor.fetchall()
            print("All tables:", all_tables)
            
            # Delete existing admin user if exists
            cursor.execute("DELETE FROM users WHERE username = %s", [username])
            print(f"Deleted existing user {username}")
            
            # Insert new admin user into 'users' table
            cursor.execute("""
                INSERT INTO users (
                    username, email, first_name, last_name,
                    password, is_staff, is_superuser, is_active,
                    date_joined
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                username, email, 'System', 'Administrator',
                hashed_password, True, True, True,
                datetime.now()
            ])
            
            print("✅ SUCCESS! Admin user created via direct SQL")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"Email: {email}")
            
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            # Try alternative table name
            try:
                cursor.execute("DELETE FROM auth_user WHERE username = %s", [username])
                cursor.execute("""
                    INSERT INTO auth_user (
                        username, email, first_name, last_name,
                        password, is_staff, is_superuser, is_active,
                        date_joined
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    username, email, 'System', 'Administrator', 
                    hashed_password, True, True, True,
                    datetime.now()
                ])
                print("✅ SUCCESS! Admin user created in auth_user table")
                print(f"Username: {username}")
                print(f"Password: {password}")
            except Exception as e2:
                print(f"❌ Alternative method failed: {e2}")

if __name__ == '__main__':
    create_admin_sql()