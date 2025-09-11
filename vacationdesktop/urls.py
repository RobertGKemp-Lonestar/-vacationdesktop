"""
URL configuration for vacationdesktop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rbac.views import create_emergency_admin, fix_existing_admin
from debug_views import debug_admin, simple_dashboard
from simple_login import emergency_login
from minimal_test import minimal_test
from db_test import db_test, model_test
from production_test import production_debug
from emergency_login_debug import emergency_login_debug
from admin_debug import admin_debug_view
from email_debug import email_debug_view
from env_debug import env_debug_view
from admin_tenant_fix import admin_tenant_fix_view

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Main RBAC dashboard
    return redirect('login')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('emergency-admin-setup/', create_emergency_admin, name='emergency_admin'),
    path('fix-admin/', fix_existing_admin, name='fix_admin'),
    path('debug-admin/', debug_admin, name='debug_admin'),
    path('simple-dashboard/', simple_dashboard, name='simple_dashboard'),
    path('emergency-login/', emergency_login, name='emergency_login'),
    path('test/', minimal_test, name='minimal_test'),
    path('db-test/', db_test, name='db_test'),
    path('model-test/', model_test, name='model_test'),
    path('production-debug/', production_debug, name='production_debug'),
    path('emergency-login-debug/', emergency_login_debug, name='emergency_login_debug'),
    path('admin-debug/', admin_debug_view, name='admin_debug_view'),
    path('email-debug/', email_debug_view, name='email_debug_view'),
    path('env-debug/', env_debug_view, name='env_debug_view'),
    path('admin-tenant-fix/', admin_tenant_fix_view, name='admin_tenant_fix_view'),
    path('', include('rbac.urls')),
    path('crm/', include('business_management.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
