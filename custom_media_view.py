from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
import os
import mimetypes

def serve_media_file(request, path):
    """Custom view to serve media files from Railway volume"""
    
    # Force use of Railway volume
    if os.path.exists('/app/media'):
        media_root = '/app/media'
    else:
        media_root = settings.MEDIA_ROOT
    
    # Build full file path
    file_path = os.path.join(media_root, path)
    
    # Security check - ensure path is within media root
    if not file_path.startswith(media_root):
        raise Http404("Invalid file path")
    
    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404(f"File not found: {path}")
    
    # Get content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Return file response
    try:
        return FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )
    except Exception as e:
        raise Http404(f"Error serving file: {str(e)}")