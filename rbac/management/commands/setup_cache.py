from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Setup Django cache table for production'

    def handle(self, *args, **options):
        """Create cache table if using database cache"""
        
        # Check if we're using database cache
        cache_config = settings.CACHES.get('default', {})
        
        if cache_config.get('BACKEND') == 'django.core.cache.backends.db.DatabaseCache':
            table_name = cache_config.get('LOCATION', 'django_cache_table')
            
            self.stdout.write(f'Setting up cache table: {table_name}')
            
            try:
                # Just create the cache table - Django will handle if it already exists
                call_command('createcachetable', table_name)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully set up cache table: {table_name}')
                )
            except Exception as e:
                # Table might already exist
                self.stdout.write(
                    self.style.WARNING(f'Cache table setup result: {e}')
                )
        else:
            self.stdout.write('Not using database cache - skipping cache table creation')