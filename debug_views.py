from django.http import HttpResponse
from django.shortcuts import redirect
from rbac.models import User, Role, Tenant

def debug_admin(request):
    """Debug admin user and system state"""
    try:
        # Get admin user
        user = User.objects.get(username='admin')
        
        debug_info = []
        debug_info.append(f"<h2>🔍 Admin User Debug Info</h2>")
        debug_info.append(f"<p><strong>Username:</strong> {user.username}</p>")
        debug_info.append(f"<p><strong>Email:</strong> {user.email}</p>")
        debug_info.append(f"<p><strong>Is Staff:</strong> {user.is_staff}</p>")
        debug_info.append(f"<p><strong>Is Superuser:</strong> {user.is_superuser}</p>")
        debug_info.append(f"<p><strong>Is Active:</strong> {user.is_active}</p>")
        
        # Check role
        if hasattr(user, 'role') and user.role:
            debug_info.append(f"<p><strong>Role:</strong> {user.role.name}</p>")
            debug_info.append(f"<p><strong>Role Level:</strong> {user.role.hierarchy_level}</p>")
        else:
            debug_info.append(f"<p><strong>Role:</strong> ❌ NO ROLE ASSIGNED</p>")
        
        # Check tenant
        if hasattr(user, 'tenant') and user.tenant:
            debug_info.append(f"<p><strong>Tenant:</strong> {user.tenant.name}</p>")
            debug_info.append(f"<p><strong>Tenant Active:</strong> {user.tenant.is_active}</p>")
        else:
            debug_info.append(f"<p><strong>Tenant:</strong> ❌ NO TENANT ASSIGNED</p>")
        
        # Check roles in system
        debug_info.append(f"<h3>📋 Available Roles:</h3>")
        roles = Role.objects.all()
        for role in roles:
            debug_info.append(f"<p>- {role.name} (Level: {role.hierarchy_level})</p>")
        
        # Check tenants
        debug_info.append(f"<h3>🏢 Available Tenants:</h3>")
        tenants = Tenant.objects.all()
        for tenant in tenants:
            debug_info.append(f"<p>- {tenant.name} (Active: {tenant.is_active})</p>")
        
        debug_info.append(f"<hr>")
        debug_info.append(f"<p><strong>Total Users:</strong> {User.objects.count()}</p>")
        debug_info.append(f"<p><strong>Total Roles:</strong> {Role.objects.count()}</p>")
        debug_info.append(f"<p><strong>Total Tenants:</strong> {Tenant.objects.count()}</p>")
        
        return HttpResponse(''.join(debug_info))
        
    except User.DoesNotExist:
        return HttpResponse("❌ Admin user not found!")
    except Exception as e:
        return HttpResponse(f"❌ DEBUG ERROR: {str(e)}")


def simple_dashboard(request):
    """Simple dashboard that bypasses complex logic"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return HttpResponse(f"""
    <h2>✅ LOGIN SUCCESSFUL!</h2>
    <p>Welcome, <strong>{request.user.username}</strong>!</p>
    <p>Email: {request.user.email}</p>
    <p>Full Name: {request.user.get_full_name()}</p>
    <p>Staff: {request.user.is_staff}</p>
    <p>Superuser: {request.user.is_superuser}</p>
    <hr>
    <p><a href="/logout/">Logout</a></p>
    <p><a href="/debug-admin/">Debug Info</a></p>
    """)