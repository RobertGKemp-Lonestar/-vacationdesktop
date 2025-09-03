from django.http import HttpResponse
import sys
import traceback

def production_debug(request):
    """Debug production-specific issues"""
    try:
        debug_info = []
        debug_info.append(f"<h2>🔍 Production Debug Info</h2>")
        debug_info.append(f"<p><strong>Python Version:</strong> {sys.version}</p>")
        debug_info.append(f"<p><strong>Python Path:</strong> {sys.path[:3]}...</p>")
        
        # Test Django version
        import django
        debug_info.append(f"<p><strong>Django Version:</strong> {django.get_version()}</p>")
        
        # Test get_user_model import
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            debug_info.append(f"<p>✅ get_user_model() works: {User}</p>")
            
            # Test User model access
            try:
                count = User.objects.count()
                debug_info.append(f"<p>✅ User.objects.count() works: {count}</p>")
            except Exception as e:
                debug_info.append(f"<p>❌ User.objects.count() failed: {str(e)}</p>")
                
        except Exception as e:
            debug_info.append(f"<p>❌ get_user_model() failed: {str(e)}</p>")
        
        # Test rbac models import
        try:
            from rbac.models import Role, Tenant
            debug_info.append(f"<p>✅ rbac.models import works</p>")
            
            role_count = Role.objects.count()
            tenant_count = Tenant.objects.count()
            debug_info.append(f"<p>✅ Role count: {role_count}, Tenant count: {tenant_count}</p>")
            
        except Exception as e:
            debug_info.append(f"<p>❌ rbac models failed: {str(e)}</p>")
            debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Production Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)