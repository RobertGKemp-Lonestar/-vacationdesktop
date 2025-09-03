from django.http import HttpResponse

def db_test(request):
    """Test database connectivity without importing our models"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        return HttpResponse(f"""
        <h2>✅ Database Connection Test</h2>
        <p>Database is connected! Result: {result}</p>
        <hr>
        <p>Now let's test our models...</p>
        """)
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Database Connection Failed</h2>
        <p>Error: {str(e)}</p>
        """)


def model_test(request):
    """Test importing our models"""
    try:
        # Test basic imports
        from django.contrib.auth.models import User as DjangoUser
        django_user_count = DjangoUser.objects.count()
        
        result = [f"<h2>🔍 Model Import Test</h2>"]
        result.append(f"<p>✅ Django User model: {django_user_count} users</p>")
        
        # Test our custom models one by one
        try:
            from rbac.models import Role
            role_count = Role.objects.count()
            result.append(f"<p>✅ Role model: {role_count} roles</p>")
        except Exception as e:
            result.append(f"<p>❌ Role model error: {str(e)}</p>")
        
        try:
            from rbac.models import Tenant
            tenant_count = Tenant.objects.count()
            result.append(f"<p>✅ Tenant model: {tenant_count} tenants</p>")
        except Exception as e:
            result.append(f"<p>❌ Tenant model error: {str(e)}</p>")
        
        try:
            from rbac.models import User
            user_count = User.objects.count()
            result.append(f"<p>✅ Custom User model: {user_count} users</p>")
        except Exception as e:
            result.append(f"<p>❌ Custom User model error: {str(e)}</p>")
        
        return HttpResponse(''.join(result))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Model Import Failed</h2>
        <p>Error: {str(e)}</p>
        """)