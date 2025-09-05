"""
User impersonation functionality for support purposes
Allows SUPER_ADMIN, SYSTEM_ADMIN, and HELPDESK_USER to impersonate other users
"""
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.urls import reverse
from rbac.models import Tenant, AuditLog
from django.utils import timezone
from .impersonation_tokens import ImpersonationTokenManager

User = get_user_model()

def can_impersonate(user, target_user):
    """Check if user has permission to impersonate target_user"""
    if not user.is_authenticated:
        return False
    
    # Only staff roles can impersonate
    if user.role.name not in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        return False
    
    # If target_user is None, just check if user has general impersonation permission
    if target_user is None:
        return True  # Basic permission check passed above
    
    # Can't impersonate yourself
    if user == target_user:
        return False
    
    # SUPER_ADMIN can impersonate anyone
    if user.role.name == 'SUPER_ADMIN':
        return True
    
    # SYSTEM_ADMIN can impersonate anyone except SUPER_ADMIN
    if user.role.name == 'SYSTEM_ADMIN':
        return target_user.role.name != 'SUPER_ADMIN'
    
    # HELPDESK_USER can only impersonate CLIENT_ADMIN and CLIENT_USER
    if user.role.name == 'HELPDESK_USER':
        return target_user.role.name in ['CLIENT_ADMIN', 'CLIENT_USER']
    
    return False

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def impersonate_tenant_users(request, tenant_id):
    """Show users in a tenant that can be impersonated"""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Permission check
    if not can_impersonate(request.user, None):
        return HttpResponseForbidden("You don't have permission to impersonate users.")
    
    # Get users in this tenant based on role permissions
    if request.user.role.name == 'SUPER_ADMIN':
        # Can see all users including system users
        users = User.objects.filter(tenant=tenant).order_by('role__hierarchy_level', 'username')
        system_users = User.objects.filter(tenant__isnull=True).exclude(id=request.user.id).order_by('role__hierarchy_level', 'username')
    elif request.user.role.name == 'SYSTEM_ADMIN':
        # Can see tenant users and system users except SUPER_ADMIN
        users = User.objects.filter(tenant=tenant).order_by('role__hierarchy_level', 'username')
        system_users = User.objects.filter(
            tenant__isnull=True
        ).exclude(
            id=request.user.id
        ).exclude(
            role__name='SUPER_ADMIN'
        ).order_by('role__hierarchy_level', 'username')
    else:  # HELPDESK_USER
        # Can only see client users
        users = User.objects.filter(
            tenant=tenant,
            role__name__in=['CLIENT_ADMIN', 'CLIENT_USER']
        ).order_by('role__hierarchy_level', 'username')
        system_users = User.objects.none()
    
    context = {
        'tenant': tenant,
        'users': users,
        'system_users': system_users,
        'current_user': request.user,
    }
    
    return render(request, 'rbac/impersonate_users.html', context)

@login_required
def start_impersonation(request, user_id):
    """Start impersonating a user with token-based session"""
    target_user = get_object_or_404(User, id=user_id)
    
    # Permission check
    if not can_impersonate(request.user, target_user):
        messages.error(request, f"You don't have permission to impersonate {target_user.username}.")
        return redirect('staff_client_management')
    
    # Create impersonation token
    token = ImpersonationTokenManager.create_token(
        original_user_id=request.user.id,
        target_user_id=target_user.id,
        original_username=request.user.username,
        target_username=target_user.username
    )
    
    # Log the impersonation start
    AuditLog.objects.create(
        user=request.user,
        tenant=target_user.tenant,
        action='IMPERSONATION_START',
        resource_type='User',
        resource_id=str(target_user.id),
        details={
            'impersonated_user': target_user.username,
            'impersonated_role': target_user.role.name,
            'impersonated_tenant': target_user.tenant.name if target_user.tenant else 'System',
            'token': token
        },
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(
        request, 
        f'Starting impersonation of {target_user.get_full_name() or target_user.username} '
        f'({target_user.role.get_name_display()}) in new tab'
    )
    
    # Redirect to dashboard with impersonation token
    dashboard_url = reverse('dashboard')
    impersonation_url = f"{dashboard_url}?imp_token={token}"
    
    return redirect(impersonation_url)

@login_required
def stop_impersonation(request):
    """Stop impersonating and return to original user"""
    # Check for token-based impersonation
    impersonation_token = request.GET.get('imp_token') or request.POST.get('imp_token')
    
    if not impersonation_token:
        messages.error(request, "No active impersonation session found.")
        return redirect('dashboard')
    
    token_data = ImpersonationTokenManager.get_token_data(impersonation_token)
    
    if not token_data:
        messages.error(request, "Invalid or expired impersonation session.")
        return redirect('dashboard')
    
    # Get original user
    try:
        original_user = User.objects.get(id=token_data['original_user_id'])
    except User.DoesNotExist:
        messages.error(request, "Original user not found.")
        return redirect('login')
    
    # Calculate duration
    started_at = timezone.datetime.fromisoformat(token_data['created_at'])
    duration_minutes = int((timezone.now() - started_at).total_seconds() / 60)
    
    # Log the impersonation end
    AuditLog.objects.create(
        user=original_user,  # Log under original user
        tenant=request.user.tenant if request.user.tenant else None,
        action='IMPERSONATION_END',
        resource_type='User',
        resource_id=str(request.user.id),
        details={
            'impersonated_user': token_data['target_username'],
            'duration_minutes': duration_minutes,
            'token': impersonation_token
        },
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Invalidate the token
    ImpersonationTokenManager.invalidate_token(impersonation_token)
    
    messages.success(request, f'Stopped impersonating. Returning to your original session...')
    
    # Redirect to staff dashboard without token
    return redirect('staff_dashboard')

def is_impersonating(request):
    """Check if current session is impersonating another user"""
    # Check for token-based impersonation
    impersonation_token = request.GET.get('imp_token') or request.POST.get('imp_token')
    if impersonation_token:
        token_data = ImpersonationTokenManager.get_token_data(impersonation_token)
        return token_data is not None
    
    # Fallback to session-based (for backward compatibility)
    return 'impersonation' in request.session

def get_impersonation_info(request):
    """Get information about current impersonation session"""
    # Check for token-based impersonation first
    impersonation_token = request.GET.get('imp_token') or request.POST.get('imp_token')
    if impersonation_token:
        token_data = ImpersonationTokenManager.get_token_data(impersonation_token)
        if token_data:
            return {
                'original_user_id': token_data['original_user_id'],
                'original_username': token_data['original_username'],
                'impersonated_user_id': token_data['target_user_id'],
                'impersonated_username': token_data['target_username'],
                'started_at': token_data['created_at'],
                'token': impersonation_token
            }
    
    # Fallback to session-based
    return request.session.get('impersonation')