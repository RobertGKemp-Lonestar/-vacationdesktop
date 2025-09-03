from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rbac.models import Role, Permission, RolePermission
import traceback

def admin_debug_view(request):
    """Debug admin user and RBAC status in production"""
    try:
        debug_info = []
        debug_info.append(f"<h2>🔍 Admin User Debug</h2>")
        
        User = get_user_model()
        
        # Check admin user
        try:
            admin_user = User.objects.get(username='admin')
            debug_info.append(f"<h3>Admin User Details:</h3>")
            debug_info.append(f"<p><strong>Username:</strong> {admin_user.username}</p>")
            debug_info.append(f"<p><strong>Email:</strong> {admin_user.email}</p>")
            debug_info.append(f"<p><strong>First Name:</strong> {admin_user.first_name}</p>")
            debug_info.append(f"<p><strong>Last Name:</strong> {admin_user.last_name}</p>")
            debug_info.append(f"<p><strong>Is Active:</strong> {admin_user.is_active}</p>")
            debug_info.append(f"<p><strong>Is Staff:</strong> {admin_user.is_staff}</p>")
            debug_info.append(f"<p><strong>Is Superuser:</strong> {admin_user.is_superuser}</p>")
            debug_info.append(f"<p><strong>Role Object:</strong> {admin_user.role}</p>")
            debug_info.append(f"<p><strong>Role Name:</strong> {admin_user.role.name if admin_user.role else 'None'}</p>")
            debug_info.append(f"<p><strong>Tenant:</strong> {admin_user.tenant}</p>")
            
            # Check all user fields
            debug_info.append(f"<h3>All User Model Fields:</h3>")
            for field in admin_user._meta.fields:
                try:
                    value = getattr(admin_user, field.name)
                    debug_info.append(f"<p><strong>{field.name}:</strong> {value}</p>")
                except Exception as e:
                    debug_info.append(f"<p><strong>{field.name}:</strong> Error getting value: {e}</p>")
            
        except User.DoesNotExist:
            debug_info.append(f"<p>❌ Admin user not found</p>")
        
        # Check roles
        debug_info.append(f"<h3>All Roles:</h3>")
        roles = Role.objects.all().order_by('hierarchy_level')
        for role in roles:
            perm_count = RolePermission.objects.filter(role=role).count()
            debug_info.append(f"<p><strong>{role.name}:</strong> {role.description} (Level {role.hierarchy_level}) - {perm_count} permissions</p>")
        
        # Check permissions
        total_permissions = Permission.objects.count()
        debug_info.append(f"<h3>Permissions:</h3>")
        debug_info.append(f"<p><strong>Total permissions in system:</strong> {total_permissions}</p>")
        
        # Check SUPER_ADMIN role specifically
        try:
            super_admin_role = Role.objects.get(name='SUPER_ADMIN')
            super_admin_perms = RolePermission.objects.filter(role=super_admin_role).count()
            debug_info.append(f"<h3>SUPER_ADMIN Role:</h3>")
            debug_info.append(f"<p><strong>Role:</strong> {super_admin_role}</p>")
            debug_info.append(f"<p><strong>Description:</strong> {super_admin_role.description}</p>")
            debug_info.append(f"<p><strong>Hierarchy Level:</strong> {super_admin_role.hierarchy_level}</p>")
            debug_info.append(f"<p><strong>Permissions Count:</strong> {super_admin_perms}</p>")
        except Role.DoesNotExist:
            debug_info.append(f"<p>❌ SUPER_ADMIN role not found</p>")
        
        # Try to run the fix commands
        debug_info.append(f"<h3>Attempting Admin Role Fix:</h3>")
        try:
            if admin_user and admin_user.role and admin_user.role.name != 'SUPER_ADMIN':
                super_admin_role = Role.objects.get(name='SUPER_ADMIN')
                admin_user.role = super_admin_role
                admin_user.save()
                debug_info.append(f"<p>✅ Fixed admin user role to SUPER_ADMIN</p>")
                debug_info.append(f"<p><strong>New role:</strong> {admin_user.role}</p>")
            else:
                debug_info.append(f"<p>Admin role appears correct or admin user not found</p>")
        except Exception as e:
            debug_info.append(f"<p>❌ Error fixing admin role: {str(e)}</p>")
            debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Admin Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)