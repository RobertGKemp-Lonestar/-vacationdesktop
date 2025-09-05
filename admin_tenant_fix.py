from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rbac.models import Role
import traceback

def admin_tenant_fix_view(request):
    """Manually fix admin tenant assignment via web endpoint"""
    debug_info = []
    debug_info.append(f"<h2>🏢 Admin Tenant Fix</h2>")
    
    try:
        User = get_user_model()
        
        # Get the admin user
        try:
            admin_user = User.objects.get(username='admin')
            debug_info.append(f"<p>✅ Found admin user: {admin_user.username}</p>")
            debug_info.append(f"<p><strong>Current role:</strong> {admin_user.role}</p>")
            debug_info.append(f"<p><strong>Current tenant:</strong> {admin_user.tenant}</p>")
            
            # Check if user has SUPER_ADMIN role
            if admin_user.role and admin_user.role.name == 'SUPER_ADMIN':
                if admin_user.tenant is not None:
                    old_tenant = admin_user.tenant
                    admin_user.tenant = None
                    admin_user.save()
                    
                    debug_info.append(f"<h3>✅ Fixed admin tenant assignment!</h3>")
                    debug_info.append(f"<p><strong>Changed from:</strong> {old_tenant}</p>")
                    debug_info.append(f"<p><strong>Changed to:</strong> None (system-wide access)</p>")
                    debug_info.append(f"<p style='color: green;'><strong>SUCCESS:</strong> Admin user now has system-wide access</p>")
                else:
                    debug_info.append(f"<p>✅ Admin user tenant is already correctly set to None</p>")
            else:
                debug_info.append(f"<p style='color: orange;'>⚠️ Admin user does not have SUPER_ADMIN role: {admin_user.role}</p>")
                
        except User.DoesNotExist:
            debug_info.append(f"<p style='color: red;'>❌ Admin user not found</p>")
            
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Admin Tenant Fix Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)