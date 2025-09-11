"""
Test file upload functionality
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from rbac.models import Tenant


class Command(BaseCommand):
    help = 'Test file upload functionality for tenant logos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Testing file upload functionality...'))
        
        # Check media settings
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        self.stdout.write(f'MEDIA_ROOT: {media_root}')
        
        if not media_root:
            self.stdout.write(self.style.ERROR('❌ MEDIA_ROOT not configured'))
            return
            
        # Check if media directory exists and is writable
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f'❌ Media directory does not exist: {media_root}'))
            return
            
        if not os.access(media_root, os.W_OK):
            self.stdout.write(self.style.ERROR(f'❌ Media directory is not writable: {media_root}'))
            return
            
        # Check tenant_logos directory
        tenant_logos_dir = os.path.join(media_root, 'tenant_logos')
        if not os.path.exists(tenant_logos_dir):
            try:
                os.makedirs(tenant_logos_dir, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'✅ Created tenant_logos directory: {tenant_logos_dir}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Cannot create tenant_logos directory: {e}'))
                return
                
        # Test creating a simple file
        test_file_path = os.path.join(tenant_logos_dir, 'test_upload.txt')
        try:
            with open(test_file_path, 'w') as f:
                f.write('Test upload file')
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully created test file: {test_file_path}'))
            
            # Clean up
            os.remove(test_file_path)
            self.stdout.write(self.style.SUCCESS('✅ Test file cleaned up'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cannot create test file: {e}'))
            return
            
        # Test with an actual tenant if available
        try:
            tenant = Tenant.objects.first()
            if tenant:
                self.stdout.write(f'Testing with tenant: {tenant.name}')
                
                # Create a dummy image file content
                dummy_content = ContentFile(b'dummy image content', name='test_logo.jpg')
                
                # Try to save it to the tenant
                original_logo = tenant.logo
                tenant.logo.save('test_logo.jpg', dummy_content, save=True)
                
                if tenant.logo and os.path.exists(tenant.logo.path):
                    self.stdout.write(self.style.SUCCESS(f'✅ Successfully saved logo to: {tenant.logo.path}'))
                    
                    # Clean up - restore original logo
                    if tenant.logo != original_logo:
                        if os.path.exists(tenant.logo.path):
                            os.remove(tenant.logo.path)
                        tenant.logo = original_logo
                        tenant.save()
                        self.stdout.write(self.style.SUCCESS('✅ Restored original tenant logo'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Failed to save tenant logo'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ No tenants found to test with'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing tenant logo save: {e}'))
            
        self.stdout.write(self.style.SUCCESS('🧪 File upload test complete'))