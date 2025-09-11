"""
Debug command to check media directory setup and permissions
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Debug media directory setup and permissions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Debugging media configuration...'))
        
        # Check MEDIA_ROOT setting
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        self.stdout.write(f'MEDIA_ROOT: {media_root}')
        
        # Check MEDIA_URL setting
        media_url = getattr(settings, 'MEDIA_URL', None)
        self.stdout.write(f'MEDIA_URL: {media_url}')
        
        if media_root:
            # Check if directory exists
            if os.path.exists(media_root):
                self.stdout.write(self.style.SUCCESS(f'✅ Media directory exists: {media_root}'))
                
                # Check if writable
                test_file = os.path.join(media_root, '.write_test')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    self.stdout.write(self.style.SUCCESS('✅ Media directory is writable'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Media directory is not writable: {e}'))
                
                # Check tenant_logos subdirectory
                tenant_logos_dir = os.path.join(media_root, 'tenant_logos')
                if os.path.exists(tenant_logos_dir):
                    self.stdout.write(self.style.SUCCESS('✅ tenant_logos directory exists'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️ tenant_logos directory does not exist'))
                    try:
                        os.makedirs(tenant_logos_dir, exist_ok=True)
                        self.stdout.write(self.style.SUCCESS('✅ Created tenant_logos directory'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'❌ Cannot create tenant_logos directory: {e}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Media directory does not exist: {media_root}'))
                try:
                    os.makedirs(media_root, exist_ok=True)
                    self.stdout.write(self.style.SUCCESS(f'✅ Created media directory: {media_root}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Cannot create media directory: {e}'))
        else:
            self.stdout.write(self.style.ERROR('❌ MEDIA_ROOT not configured'))
        
        # Check permissions
        if media_root and os.path.exists(media_root):
            stat_info = os.stat(media_root)
            permissions = oct(stat_info.st_mode)[-3:]
            self.stdout.write(f'📁 Directory permissions: {permissions}')
            
        self.stdout.write(self.style.SUCCESS('🔍 Media debug complete'))