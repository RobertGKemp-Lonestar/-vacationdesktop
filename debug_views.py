from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from rbac.models import Role, Tenant

User = get_user_model()

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
    <!DOCTYPE html>
    <html>
    <head>
        <title>VacationDesktop - Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="#">VacationDesktop</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/logout/">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h4>✅ Welcome to VacationDesktop!</h4>
                        </div>
                        <div class="card-body">
                            <p><strong>Welcome back, {request.user.get_full_name() or request.user.username}!</strong></p>
                            <p><strong>Email:</strong> {request.user.email}</p>
                            <p><strong>Role:</strong> {request.user.role.name if hasattr(request.user, 'role') and request.user.role else 'No role'}</p>
                            <p><strong>Organization:</strong> {request.user.tenant.name if hasattr(request.user, 'tenant') and request.user.tenant else 'No tenant'}</p>
                            
                            <hr>
                            
                            <h5>🎉 Deployment Successful!</h5>
                            <p>Your VacationDesktop multi-tenant RBAC system is now running in production!</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-4">
                                    <div class="card border-primary">
                                        <div class="card-body text-center">
                                            <h6>System Status</h6>
                                            <span class="badge bg-success">✅ Online</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card border-info">
                                        <div class="card-body text-center">
                                            <h6>Your Access Level</h6>
                                            <span class="badge bg-primary">Super Administrator</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card border-warning">
                                        <div class="card-body text-center">
                                            <h6>Next Steps</h6>
                                            <span class="badge bg-warning">Configure Features</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <hr>
                            
                            <h6>Quick Actions:</h6>
                            <div class="btn-group" role="group">
                                <a href="/admin/" class="btn btn-outline-primary btn-sm">Django Admin</a>
                                <a href="/debug-admin/" class="btn btn-outline-info btn-sm">System Debug</a>
                                <a href="/logout/" class="btn btn-outline-danger btn-sm">Logout</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)