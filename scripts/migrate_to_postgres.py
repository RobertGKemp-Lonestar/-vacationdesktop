#!/usr/bin/env python
"""
Migration script to move from SQLite to PostgreSQL
"""
import os
import sys
import django
from django.core.management import call_command
from django.core import serializers
from django.apps import apps

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacationdesktop.settings')
django.setup()

def export_data():
    """Export all data from current database to fixtures"""
    print("Exporting data from SQLite...")
    
    # Get all models
    models_to_export = []
    for app in apps.get_app_configs():
        if app.name in ['rbac']:  # Only export our custom apps
            for model in app.get_models():
                models_to_export.append(f"{app.label}.{model._meta.model_name}")
    
    if models_to_export:
        call_command(
            'dumpdata', 
            *models_to_export,
            '--natural-foreign',
            '--natural-primary',
            '--output=data_backup.json',
            '--indent=2'
        )
        print(f"✅ Data exported to data_backup.json")
        print(f"📊 Exported models: {', '.join(models_to_export)}")
    else:
        print("ℹ️  No custom data to export")

def import_data():
    """Import data fixtures into new database"""
    if os.path.exists('data_backup.json'):
        print("Importing data into PostgreSQL...")
        call_command('loaddata', 'data_backup.json')
        print("✅ Data imported successfully")
    else:
        print("ℹ️  No backup file found to import")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "export":
            export_data()
        elif sys.argv[1] == "import":
            import_data()
        else:
            print("Usage: python migrate_to_postgres.py [export|import]")
    else:
        print("Usage: python migrate_to_postgres.py [export|import]")
        print("First run: python migrate_to_postgres.py export")
        print("Then switch database settings and run: python migrate_to_postgres.py import")