from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Verify Railway volume is working correctly'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verifying Railway Volume Configuration...")
        
        # Check media root setting
        self.stdout.write(f"📁 MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"📁 MEDIA_URL: {settings.MEDIA_URL}")
        
        # Check if volume exists
        if os.path.exists('/app/media'):
            self.stdout.write(self.style.SUCCESS("✅ Railway volume /app/media exists"))
        else:
            self.stdout.write(self.style.ERROR("❌ Railway volume /app/media does NOT exist"))
        
        # Check media root
        if os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(self.style.SUCCESS(f"✅ MEDIA_ROOT directory exists: {settings.MEDIA_ROOT}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ MEDIA_ROOT directory does NOT exist: {settings.MEDIA_ROOT}"))
            
        # Check tenant_logos directory
        tenant_logos_dir = os.path.join(settings.MEDIA_ROOT, 'tenant_logos')
        if os.path.exists(tenant_logos_dir):
            self.stdout.write(self.style.SUCCESS(f"✅ tenant_logos directory exists: {tenant_logos_dir}"))
            
            # List files in tenant_logos directory
            try:
                files = os.listdir(tenant_logos_dir)
                if files:
                    self.stdout.write(f"📄 Files in tenant_logos directory:")
                    for file in files:
                        file_path = os.path.join(tenant_logos_dir, file)
                        file_size = os.path.getsize(file_path)
                        self.stdout.write(f"   - {file} ({file_size} bytes)")
                else:
                    self.stdout.write("📄 tenant_logos directory is empty")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Cannot list files in tenant_logos: {e}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ tenant_logos directory does NOT exist: {tenant_logos_dir}"))
        
        # Test write permissions
        test_file_path = os.path.join(settings.MEDIA_ROOT, 'test_write.txt')
        try:
            with open(test_file_path, 'w') as f:
                f.write("test")
            os.remove(test_file_path)
            self.stdout.write(self.style.SUCCESS("✅ MEDIA_ROOT is writable"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ MEDIA_ROOT is NOT writable: {e}"))
            
        # Check if volume is properly mounted
        if settings.MEDIA_ROOT == '/app/media':
            self.stdout.write(self.style.SUCCESS("✅ Using Railway volume path"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Not using Railway volume. Using: {settings.MEDIA_ROOT}"))