from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import User, Role, Permission, Tenant, AuditLog, SupportTicket, TicketComment
from .forms import AddUserForm, EditUserForm, ChangeUserPasswordForm


def login_view(request):
    """Custom login view with RBAC support"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Log the login
            AuditLog.objects.create(
                user=user,
                tenant=user.tenant,
                action='LOGIN',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                details={'login_method': 'password'}
            )
            
            # Update last login IP
            user.last_login_ip = get_client_ip(request)
            user.save()
            
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'rbac/login.html')


def logout_view(request):
    """Custom logout view"""
    if request.user.is_authenticated:
        # Log the logout
        AuditLog.objects.create(
            user=request.user,
            tenant=request.user.tenant,
            action='LOGOUT',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
    
    return redirect('login')


@login_required
def dashboard_view(request):
    """Main dashboard view - customized per role"""
    user = request.user
    
    # Helpdesk users get a specialized dashboard
    if user.role.name == 'HELPDESK_USER':
        return helpdesk_dashboard_view(request)
    
    context = {
        'user': user,
        'stats': {},
    }
    
    # System-level statistics for system users
    if user.is_system_user():
        context['stats'] = {
            'total_tenants': Tenant.objects.count(),
            'active_tenants': Tenant.objects.filter(is_active=True).count(),
            'total_users': User.objects.count(),
            'system_users': User.objects.filter(role__is_system_role=True).count(),
        }
    
    # Tenant-level statistics for client users
    elif user.tenant:
        context['stats'] = {
            'tenant_users': User.objects.filter(tenant=user.tenant).count(),
            'active_campaigns': 0,  # Placeholder for future functionality
            'total_contacts': 0,    # Placeholder for future functionality
            'pending_invoices': 0,  # Placeholder for future functionality
        }
    
    # Recent activity
    context['recent_activity'] = AuditLog.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    return render(request, 'rbac/dashboard.html', context)


@login_required
def helpdesk_dashboard_view(request):
    """Specialized dashboard for helpdesk users with embedded ticket management"""
    user = request.user
    
    # Get filter parameters (same as ticket_list_view)
    status_filter = request.GET.get('status', '')  # Show all tickets by default
    priority_filter = request.GET.get('priority', '')
    assigned_filter = request.GET.get('assigned', '')
    search = request.GET.get('search', '')
    
    # Build ticket query
    tickets = SupportTicket.objects.all()
    
    # Apply filters
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if assigned_filter == 'me':
        tickets = tickets.filter(assigned_to=user)
    elif assigned_filter == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    if search:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(tenant__name__icontains=search)
        )
    
    tickets = tickets.order_by('-created_at')
    
    # Pagination for tickets
    paginator = Paginator(tickets, 15)  # Smaller page size for dashboard
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get ticket statistics
    context = {
        'user': user,
        'tickets': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_filter': assigned_filter,
        'search': search,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_LEVELS,
        
        # Dashboard statistics
        'stats': {
            'open_tickets': SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
            'pending_tickets': SupportTicket.objects.filter(status='PENDING').count(),
            'my_tickets': SupportTicket.objects.filter(assigned_to=user, status__in=['OPEN', 'IN_PROGRESS']).count(),
            'unassigned_tickets': SupportTicket.objects.filter(assigned_to__isnull=True, status__in=['OPEN', 'IN_PROGRESS']).count(),
            'high_priority': SupportTicket.objects.filter(priority__in=['HIGH', 'URGENT'], status__in=['OPEN', 'IN_PROGRESS']).count(),
        },
        
        # Quick access data
        'recent_tickets': SupportTicket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS', 'PENDING']
        ).order_by('-created_at')[:5],
        
        'urgent_tickets': SupportTicket.objects.filter(
            priority='URGENT', 
            status__in=['OPEN', 'IN_PROGRESS']
        ).order_by('-created_at')[:3],
    }
    
    return render(request, 'rbac/helpdesk_dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'rbac/profile.html', {'user': request.user})


@login_required
def profile_edit_view(request):
    """Profile editing view"""
    from .forms import UserProfileForm
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Log the profile update
            AuditLog.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                action='UPDATE',
                resource_type='User Profile',
                resource_id=str(request.user.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                details={'fields_updated': list(form.changed_data)}
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'rbac/profile_edit.html', {
        'form': form,
        'user': request.user
    })


@login_required
def password_change_view(request):
    """Password change view"""
    from django.contrib.auth import update_session_auth_hash
    from .forms import CustomPasswordChangeForm
    
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            
            # Log the password change
            AuditLog.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                action='UPDATE',
                resource_type='User Password',
                resource_id=str(request.user.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                details={'action': 'password_changed'}
            )
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'rbac/password_change.html', {
        'form': form,
        'user': request.user
    })


def password_reset_request_view(request):
    """Password reset request view"""
    from .forms import CustomPasswordResetForm
    
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,  # Use default from settings
                email_template_name='rbac/password_reset_email.html',
                subject_template_name='rbac/password_reset_subject.txt',
                html_email_template_name='rbac/password_reset_email.html',
            )
            messages.success(request, 'Password reset email has been sent! Check your inbox.')
            return redirect('password_reset_done')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'rbac/password_reset_request.html', {
        'form': form
    })


def password_reset_done_view(request):
    """Password reset done view"""
    return render(request, 'rbac/password_reset_done.html')


def password_reset_confirm_view(request, uidb64, token):
    """Password reset confirmation view"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth import get_user_model
    from .forms import CustomSetPasswordForm
    
    UserModel = get_user_model()
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                
                # Log the password reset
                AuditLog.objects.create(
                    user=user,
                    tenant=user.tenant,
                    action='UPDATE',
                    resource_type='User Password',
                    resource_id=str(user.id),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                    details={'action': 'password_reset_completed'}
                )
                
                messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
                return redirect('password_reset_complete')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = CustomSetPasswordForm(user)
    else:
        validlink = False
        form = None
        messages.error(request, 'The password reset link is invalid or has expired.')
    
    return render(request, 'rbac/password_reset_confirm.html', {
        'form': form,
        'validlink': validlink,
    })


def password_reset_complete_view(request):
    """Password reset complete view"""
    return render(request, 'rbac/password_reset_complete.html')


def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# User Management Views

@login_required
def user_list_view(request):
    """List users in the current tenant"""
    # Permission check
    if not (request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN']):
        messages.error(request, 'You do not have permission to view users.')
        return redirect('dashboard')
    
    # Get users in the same tenant (or all users for system admins)
    if request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN']:
        users = User.objects.all().order_by('username')
    else:
        users = User.objects.filter(tenant=request.user.tenant).order_by('username')
    
    context = {
        'users': users,
        'can_add_user': request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN'],
        'can_edit_users': request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN'],
    }
    
    return render(request, 'rbac/user_list.html', context)


@login_required
def add_user_view(request):
    """Add a new user to the tenant"""
    # Permission check
    if not (request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN']):
        messages.error(request, 'You do not have permission to add users.')
        return redirect('user_list')
    
    if request.method == 'POST':
        form = AddUserForm(
            request.POST,
            tenant=request.user.tenant,
            requesting_user=request.user
        )
        if form.is_valid():
            user = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                action='USER_CREATE',
                resource_type='User',
                resource_id=str(user.id),
                details={
                    'created_user': user.username,
                    'role': user.role.name
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_list')
    else:
        form = AddUserForm(
            tenant=request.user.tenant,
            requesting_user=request.user
        )
    
    context = {
        'form': form,
        'title': 'Add New User',
    }
    
    return render(request, 'rbac/add_user.html', context)


@login_required
def edit_user_view(request, user_id):
    """Edit an existing user"""
    # Permission check
    if not (request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN']):
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('user_list')
    
    try:
        # Get user based on permissions
        if request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN']:
            user = User.objects.get(id=user_id)
        else:
            # Client admins can only edit users in their tenant
            user = User.objects.get(id=user_id, tenant=request.user.tenant)
    except User.DoesNotExist:
        messages.error(request, 'User not found or you do not have permission to edit this user.')
        return redirect('user_list')
    
    # Prevent users from editing themselves
    if user == request.user:
        messages.error(request, 'You cannot edit your own account here. Use Profile Settings instead.')
        return redirect('user_list')
    
    if request.method == 'POST':
        form = EditUserForm(
            request.POST,
            instance=user,
            requesting_user=request.user
        )
        if form.is_valid():
            original_data = {
                'email': user.email,
                'role': user.role.name,
                'is_active': user.is_active,
            }
            
            user = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                action='USER_UPDATE',
                resource_type='User',
                resource_id=str(user.id),
                details={
                    'updated_user': user.username,
                    'original_data': original_data,
                    'new_data': {
                        'email': user.email,
                        'role': user.role.name,
                        'is_active': user.is_active,
                    }
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('user_list')
    else:
        form = EditUserForm(
            instance=user,
            requesting_user=request.user
        )
    
    context = {
        'form': form,
        'user_to_edit': user,
        'title': f'Edit User: {user.username}',
    }
    
    return render(request, 'rbac/edit_user.html', context)


@login_required
def change_user_password_view(request, user_id):
    """Change a user's password (admin only)"""
    # Permission check - only admins can change other users' passwords
    if not (request.user.role.name in ['CLIENT_ADMIN', 'SUPER_ADMIN', 'SYSTEM_ADMIN']):
        messages.error(request, 'You do not have permission to change user passwords.')
        return redirect('user_list')
    
    try:
        # Get user based on permissions
        if request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN']:
            user = User.objects.get(id=user_id)
        else:
            # Client admins can only change passwords for users in their tenant
            user = User.objects.get(id=user_id, tenant=request.user.tenant)
    except User.DoesNotExist:
        messages.error(request, 'User not found or you do not have permission to change this password.')
        return redirect('user_list')
    
    # Prevent changing own password here
    if user == request.user:
        messages.error(request, 'Use Profile Settings to change your own password.')
        return redirect('user_list')
    
    if request.method == 'POST':
        form = ChangeUserPasswordForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                action='PASSWORD_RESET',
                resource_type='User',
                resource_id=str(user.id),
                details={
                    'target_user': user.username,
                    'changed_by_admin': True
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Password changed for user {user.username}.')
            return redirect('user_list')
    else:
        form = ChangeUserPasswordForm(user=user)
    
    context = {
        'form': form,
        'user_to_edit': user,
        'title': f'Change Password: {user.username}',
    }
    
    return render(request, 'rbac/change_user_password.html', context)


# Staff Dashboard and Support Ticket Management

@login_required
def staff_dashboard_view(request):
    """Staff dashboard for helpdesk and admin users"""
    # Permission check - only staff users
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to access the staff dashboard.')
        return redirect('dashboard')
    
    # Get ticket statistics
    context = {
        'open_tickets': SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
        'pending_tickets': SupportTicket.objects.filter(status='PENDING').count(),
        'my_tickets': SupportTicket.objects.filter(assigned_to=request.user, status__in=['OPEN', 'IN_PROGRESS']).count(),
        'recent_tickets': SupportTicket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS', 'PENDING']
        ).order_by('-created_at')[:10],
        
        # Tenant statistics
        'total_tenants': Tenant.objects.count(),
        'active_tenants': Tenant.objects.filter(is_active=True).count(),
        'trial_tenants': Tenant.objects.filter(tenant_type='TRIAL').count(),
        'prospect_tenants': Tenant.objects.filter(tenant_type='PROSPECT').count(),
    }
    
    return render(request, 'rbac/staff_dashboard.html', context)


@login_required
def ticket_list_view(request):
    """List all support tickets for staff"""
    # Permission check
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to view tickets.')
        return redirect('dashboard')
    
    # Filter options
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_filter = request.GET.get('assigned', '')
    search = request.GET.get('search', '')
    
    tickets = SupportTicket.objects.all()
    
    # Apply filters
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if assigned_filter == 'me':
        tickets = tickets.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    if search:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(tenant__name__icontains=search)
        )
    
    tickets = tickets.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tickets': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_filter': assigned_filter,
        'search': search,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_LEVELS,
    }
    
    return render(request, 'rbac/ticket_list.html', context)


@login_required
def ticket_detail_view(request, ticket_id):
    """View and manage a specific support ticket"""
    # Permission check
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to view tickets.')
        return redirect('dashboard')
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    # Handle POST requests for ticket actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_comment':
            comment_text = request.POST.get('comment', '').strip()
            comment_type = request.POST.get('comment_type', 'client')
            is_internal = (comment_type == 'internal')
            
            if comment_text:
                comment = TicketComment.objects.create(
                    ticket=ticket,
                    author=request.user,
                    comment=comment_text,
                    is_internal=is_internal
                )
                
                # Send email notification if it's a client comment and user exists
                if not is_internal and ticket.created_for and ticket.created_for.email:
                    send_ticket_notification_email(ticket, comment, 'comment')
                
                # Log the comment
                AuditLog.objects.create(
                    user=request.user,
                    tenant=ticket.tenant,
                    action='TICKET_COMMENT',
                    resource_type='SupportTicket',
                    resource_id=str(ticket.id),
                    details={
                        'ticket_number': ticket.ticket_number,
                        'is_internal': is_internal,
                        'comment_preview': comment_text[:100]
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Comment added successfully.')
            else:
                messages.error(request, 'Comment cannot be empty.')
        
        elif action == 'assign_to_me':
            if request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
                ticket.assigned_to = request.user
                if ticket.status == 'NEW':
                    ticket.status = 'OPEN'
                ticket.save()
                
                # Log the assignment
                AuditLog.objects.create(
                    user=request.user,
                    tenant=ticket.tenant,
                    action='TICKET_ASSIGN',
                    resource_type='SupportTicket',
                    resource_id=str(ticket.id),
                    details={
                        'ticket_number': ticket.ticket_number,
                        'assigned_to': request.user.username
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Ticket assigned to you and status updated to {ticket.get_status_display()}.')
        
        elif action == 'mark_resolved':
            if request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
                resolution = request.POST.get('resolution', '').strip()
                
                if resolution:
                    ticket.status = 'RESOLVED'
                    ticket.resolution = resolution
                    ticket.resolved_at = timezone.now()
                    ticket.save()
                    
                    # Add automatic resolution comment
                    resolution_comment = TicketComment.objects.create(
                        ticket=ticket,
                        author=request.user,
                        comment=f"Ticket resolved by {request.user.get_full_name() or request.user.username}:\n\n{resolution}",
                        is_internal=False
                    )
                    
                    # Send email notification to client
                    if ticket.created_for and ticket.created_for.email:
                        send_ticket_notification_email(ticket, resolution_comment, 'resolved')
                    
                    # Log the resolution
                    AuditLog.objects.create(
                        user=request.user,
                        tenant=ticket.tenant,
                        action='TICKET_RESOLVE',
                        resource_type='SupportTicket',
                        resource_id=str(ticket.id),
                        details={
                            'ticket_number': ticket.ticket_number,
                            'resolved_by': request.user.username,
                            'resolution_preview': resolution[:100]
                        },
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, 'Ticket marked as resolved.')
                else:
                    messages.error(request, 'Resolution description is required.')
        
        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            if new_status and new_status in [choice[0] for choice in SupportTicket.STATUS_CHOICES]:
                old_status = ticket.status
                ticket.status = new_status
                ticket.save()
                
                # Log the status change
                AuditLog.objects.create(
                    user=request.user,
                    tenant=ticket.tenant,
                    action='TICKET_STATUS_CHANGE',
                    resource_type='SupportTicket',
                    resource_id=str(ticket.id),
                    details={
                        'ticket_number': ticket.ticket_number,
                        'old_status': old_status,
                        'new_status': new_status
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Ticket status changed to {ticket.get_status_display()}.')
        
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    comments = ticket.comments.order_by('created_at')
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'can_assign': request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN'],
        'can_close': request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER'],
        'status_choices': SupportTicket.STATUS_CHOICES,
    }
    
    return render(request, 'rbac/ticket_detail.html', context)


@login_required
def create_ticket_view(request):
    """Create a new support ticket"""
    # Permission check
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to create tickets.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        created_for_id = request.POST.get('created_for')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'MEDIUM')
        category = request.POST.get('category', 'OTHER')
        
        if tenant_id and subject and description:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            created_for_user = None
            
            if created_for_id:
                # Ensure the selected user belongs to the selected tenant
                try:
                    created_for_user = User.objects.get(
                        id=created_for_id,
                        tenant=tenant,
                        role__is_system_role=False
                    )
                except User.DoesNotExist:
                    messages.error(request, 'Selected user not found or does not belong to the selected tenant.')
                    return redirect('create_ticket')
            
            ticket = SupportTicket.objects.create(
                tenant=tenant,
                subject=subject,
                description=description,
                priority=priority,
                category=category,
                created_by=request.user,
                created_for=created_for_user,
                status='OPEN'
            )
            
            # Send email notification to client when ticket is created
            if created_for_user and created_for_user.email:
                send_ticket_notification_email(ticket, None, 'created')
            
            # Log the creation
            AuditLog.objects.create(
                user=request.user,
                tenant=tenant,
                action='TICKET_CREATE',
                resource_type='SupportTicket',
                resource_id=str(ticket.id),
                details={
                    'ticket_number': ticket.ticket_number,
                    'subject': subject,
                    'priority': priority
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Support ticket {ticket.ticket_number} created successfully.')
            return redirect('ticket_detail', ticket_id=ticket.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    tenants = Tenant.objects.filter(is_active=True).order_by('name')
    
    context = {
        'tenants': tenants,
        'priority_choices': SupportTicket.PRIORITY_LEVELS,
        'category_choices': SupportTicket.CATEGORY_CHOICES,
    }
    
    return render(request, 'rbac/create_ticket.html', context)


@login_required
def staff_client_management_view(request):
    """Staff interface for managing client tenants and users"""
    # Permission check
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to access client management.')
        return redirect('dashboard')
    
    search = request.GET.get('search', '')
    tenant_type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    tenants = Tenant.objects.all()
    
    if search:
        tenants = tenants.filter(
            Q(name__icontains=search) |
            Q(subdomain__icontains=search) |
            Q(contact_email__icontains=search)
        )
    
    if tenant_type_filter:
        tenants = tenants.filter(tenant_type=tenant_type_filter)
    
    if status_filter:
        tenants = tenants.filter(status=status_filter)
    
    tenants = tenants.order_by('name')
    
    # Pagination
    paginator = Paginator(tenants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tenants': page_obj,
        'search': search,
        'tenant_type_filter': tenant_type_filter,
        'status_filter': status_filter,
        'tenant_type_choices': Tenant.TENANT_TYPES,
        'status_choices': Tenant.TENANT_STATUSES,
    }
    
    return render(request, 'rbac/staff_client_management.html', context)


@login_required
def create_client_user_view(request, tenant_id):
    """Create a user for a specific client tenant"""
    # Permission check
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        messages.error(request, 'You do not have permission to create client users.')
        return redirect('dashboard')
    
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role_name = request.POST.get('role', 'CLIENT_USER')
        is_tenant_admin = request.POST.get('is_tenant_admin') == 'on'
        
        if username and email and password:
            try:
                role = Role.objects.get(name=role_name)
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    tenant=tenant,
                    role=role,
                    is_tenant_admin=is_tenant_admin
                )
                
                # Log the creation
                AuditLog.objects.create(
                    user=request.user,
                    tenant=tenant,
                    action='USER_CREATE',
                    resource_type='User',
                    resource_id=str(user.id),
                    details={
                        'created_user': user.username,
                        'role': role.name,
                        'for_tenant': tenant.name,
                        'created_by_staff': True
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'User {username} created successfully for {tenant.name}.')
                return redirect('staff_client_management')
                
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get client roles only
    client_roles = Role.objects.filter(is_system_role=False).order_by('hierarchy_level')
    
    context = {
        'tenant': tenant,
        'client_roles': client_roles,
    }
    
    return render(request, 'rbac/create_client_user.html', context)


@login_required
def get_tenant_users_ajax(request):
    """AJAX endpoint to get users for a specific tenant"""
    if not request.user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    tenant_id = request.GET.get('tenant_id')
    if not tenant_id:
        return JsonResponse({'error': 'Missing tenant_id'}, status=400)
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        users = User.objects.filter(
            tenant=tenant,
            role__is_system_role=False,
            is_active=True
        ).values('id', 'username', 'first_name', 'last_name', 'email').order_by('username')
        
        user_list = []
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            display_name = full_name if full_name else user['username']
            user_list.append({
                'id': str(user['id']),
                'name': display_name,
                'email': user['email'],
                'username': user['username']
            })
        
        return JsonResponse({'users': user_list})
        
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def send_ticket_notification_email(ticket, comment=None, notification_type='comment'):
    """Send email notification to client user about ticket updates"""
    if not ticket.created_for or not ticket.created_for.email:
        return False
    
    try:
        # Prepare email context
        context = {
            'ticket': ticket,
            'user': ticket.created_for,
            'comment': comment,
            'notification_type': notification_type,
            'company_name': 'VacationDesktop',
        }
        
        # Determine subject and template based on notification type
        if notification_type == 'created':
            subject = f'New support ticket created: {ticket.ticket_number}'
            template = 'rbac/emails/ticket_created_notification.html'
        elif notification_type == 'comment':
            subject = f'Update on your support ticket {ticket.ticket_number}'
            template = 'rbac/emails/ticket_comment_notification.html'
        elif notification_type == 'resolved':
            subject = f'Your support ticket {ticket.ticket_number} has been resolved'
            template = 'rbac/emails/ticket_resolved_notification.html'
        elif notification_type == 'status_change':
            subject = f'Status update for ticket {ticket.ticket_number}'
            template = 'rbac/emails/ticket_status_notification.html'
        else:
            subject = f'Update on ticket {ticket.ticket_number}'
            template = 'rbac/emails/ticket_generic_notification.html'
        
        # Render email content
        try:
            html_message = render_to_string(template, context)
        except:
            # Fallback to simple HTML if template doesn't exist
            if notification_type == 'created':
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <p>Dear <strong>{ticket.created_for.get_full_name() or ticket.created_for.username}</strong>,</p>
                    
                    <p>A new support ticket has been created for you:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                        <p><strong>Ticket Number:</strong> {ticket.ticket_number}</p>
                        <p><strong>Subject:</strong> {ticket.subject}</p>
                        <p><strong>Priority:</strong> <span style="color: {'#dc3545' if ticket.priority == 'HIGH' else '#ffc107' if ticket.priority == 'MEDIUM' else '#6c757d'}">{ticket.get_priority_display()}</span></p>
                        <p><strong>Status:</strong> {ticket.get_status_display()}</p>
                    </div>
                    
                    <p><strong>Description:</strong></p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <p>{ticket.description.replace(chr(10), '<br>')}</p>
                    </div>
                    
                    <p>Our support team will review your request and respond as soon as possible.</p>
                    
                    <hr style="border: none; height: 1px; background-color: #dee2e6; margin: 30px 0;">
                    
                    <p>Best regards,<br>
                    <strong>The VacationDesktop Support Team</strong></p>
                </body>
                </html>
                """
            else:
                update_content = f'<div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0;"><p><strong>Latest Update:</strong></p><p>{comment.comment.replace(chr(10), "<br>") if comment else ""}</p></div>' if comment else ''
                
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <p>Dear <strong>{ticket.created_for.get_full_name() or ticket.created_for.username}</strong>,</p>
                    
                    <p>Your support ticket <strong>{ticket.ticket_number}</strong> has been updated.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                        <p><strong>Subject:</strong> {ticket.subject}</p>
                        <p><strong>Status:</strong> {ticket.get_status_display()}</p>
                        <p><strong>Priority:</strong> <span style="color: {'#dc3545' if ticket.priority == 'HIGH' else '#ffc107' if ticket.priority == 'MEDIUM' else '#6c757d'}">{ticket.get_priority_display()}</span></p>
                    </div>
                    
                    {update_content}
                    
                    <p>Please log in to your account to view the full details.</p>
                    
                    <hr style="border: none; height: 1px; background-color: #dee2e6; margin: 30px 0;">
                    
                    <p>Best regards,<br>
                    <strong>The VacationDesktop Support Team</strong></p>
                </body>
                </html>
                """
        
        # Create plain text version for email clients that don't support HTML
        import re
        plain_text_message = re.sub('<[^<]+?>', '', html_message)  # Remove all HTML tags
        plain_text_message = plain_text_message.replace('&nbsp;', ' ')  # Replace HTML entities
        plain_text_message = re.sub(r'\n\s*\n\s*\n', '\n\n', plain_text_message)  # Clean up excessive newlines
        plain_text_message = plain_text_message.strip()  # Remove leading/trailing whitespace
        
        # Send the email
        send_mail(
            subject=subject,
            message=plain_text_message,  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.created_for.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        return False
