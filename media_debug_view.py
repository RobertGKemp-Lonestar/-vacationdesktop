from django.http import HttpResponse
from django.conf import settings
import os

def media_debug_view(request):
    """Debug view to check media configuration"""
    
    debug_info = []
    debug_info.append(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    debug_info.append(f"MEDIA_URL: {settings.MEDIA_URL}")
    debug_info.append(f"DEBUG: {settings.DEBUG}")
    
    # Check if directories exist
    debug_info.append(f"\nDirectory checks:")
    debug_info.append(f"MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
    debug_info.append(f"/app/media exists: {os.path.exists('/app/media')}")
    
    tenant_logos_dir = os.path.join(settings.MEDIA_ROOT, 'tenant_logos')
    debug_info.append(f"tenant_logos dir exists: {os.path.exists(tenant_logos_dir)}")
    
    # List files if directory exists
    if os.path.exists(tenant_logos_dir):
        try:
            files = os.listdir(tenant_logos_dir)
            debug_info.append(f"\nFiles in tenant_logos:")
            for file in files:
                file_path = os.path.join(tenant_logos_dir, file)
                size = os.path.getsize(file_path)
                debug_info.append(f"  - {file} ({size} bytes)")
        except Exception as e:
            debug_info.append(f"Error listing files: {e}")
    
    # Test file access
    debug_info.append(f"\nTesting file access:")
    if os.path.exists(tenant_logos_dir):
        files = [f for f in os.listdir(tenant_logos_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            test_file = files[0]
            test_path = os.path.join(tenant_logos_dir, test_file)
            debug_info.append(f"Test file: {test_file}")
            debug_info.append(f"Full path: {test_path}")
            debug_info.append(f"File exists: {os.path.exists(test_path)}")
            debug_info.append(f"File readable: {os.access(test_path, os.R_OK)}")
    
    return HttpResponse('\n'.join(debug_info), content_type='text/plain')