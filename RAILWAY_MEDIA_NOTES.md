# Railway Media Files Handling

## Current Implementation
- Media files are stored locally on Railway's ephemeral filesystem
- Directory creation and permissions are handled in `start.sh`
- Debug command available: `python manage.py debug_media`

## Important Notes

### Ephemeral Filesystem
Railway uses ephemeral storage, meaning:
- Uploaded files are lost when the container restarts/redeploys
- This is acceptable for testing but not for production long-term

### For Production Use
Consider implementing cloud storage:
- **AWS S3** with django-storages
- **Cloudinary** for image processing
- **Google Cloud Storage**
- **Azure Blob Storage**

### Current Workaround
The current setup works for:
- Testing logo functionality
- Demonstration purposes
- Short-term usage between deployments

### Troubleshooting
1. Check Railway logs for media directory creation
2. Use `python manage.py debug_media` to check setup
3. Verify permissions with `ls -la media/`

### Future Enhancement
```python
# Example AWS S3 setup for production
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```