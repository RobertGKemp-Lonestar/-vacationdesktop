from django.http import HttpResponse
import os
import traceback

def env_debug_view(request):
    """Debug environment variables"""
    debug_info = []
    debug_info.append(f"<h2>🔧 Environment Variables Debug</h2>")
    
    try:
        # Show all EMAIL related environment variables
        debug_info.append(f"<h3>Email-Related Environment Variables:</h3>")
        
        email_vars = [
            'EMAIL_HOST',
            'EMAIL_HOST_USER', 
            'EMAIL_HOST_PASSWORD',
            'EMAIL_PORT',
            'EMAIL_USE_TLS',
            'EMAIL_USE_SSL',
            'DEFAULT_FROM_EMAIL',
            'FORCE_CONSOLE_EMAIL'
        ]
        
        for var in email_vars:
            value = os.environ.get(var, 'NOT SET')
            if 'PASSWORD' in var and value != 'NOT SET':
                value = '*' * len(value)
            debug_info.append(f"<p><strong>{var}:</strong> {value}</p>")
        
        # Show all environment variables that contain 'EMAIL' or 'MAIL'
        debug_info.append(f"<h3>All Mail-Related Environment Variables:</h3>")
        mail_vars = {k: v for k, v in os.environ.items() if 'MAIL' in k.upper() or 'EMAIL' in k.upper()}
        
        if mail_vars:
            for key, value in sorted(mail_vars.items()):
                if 'PASSWORD' in key.upper():
                    value = '*' * len(value)
                debug_info.append(f"<p><strong>{key}:</strong> {value}</p>")
        else:
            debug_info.append(f"<p>No mail-related environment variables found</p>")
        
        # Test the decouple config function
        debug_info.append(f"<h3>Testing django-decouple Config:</h3>")
        try:
            from decouple import config
            
            debug_info.append(f"<p><strong>config('EMAIL_HOST', default='NOT_FOUND'):</strong> {config('EMAIL_HOST', default='NOT_FOUND')}</p>")
            debug_info.append(f"<p><strong>config('EMAIL_PORT', default='NOT_FOUND'):</strong> {config('EMAIL_PORT', default='NOT_FOUND')}</p>")
            debug_info.append(f"<p><strong>config('EMAIL_USE_TLS', default='NOT_FOUND'):</strong> {config('EMAIL_USE_TLS', default='NOT_FOUND')}</p>")
            
        except Exception as config_e:
            debug_info.append(f"<p>❌ Error testing config: {str(config_e)}</p>")
        
        # Show Railway-specific variables
        debug_info.append(f"<h3>Railway Environment Info:</h3>")
        railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'PORT']
        for var in railway_vars:
            value = os.environ.get(var, 'NOT SET')
            debug_info.append(f"<p><strong>{var}:</strong> {value}</p>")
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Environment Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)