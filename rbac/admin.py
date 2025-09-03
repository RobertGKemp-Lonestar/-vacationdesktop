from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Tenant, Role, Permission, RolePermission, UserPermissionOverride, AuditLog,
    AccountStatus, ClientAccount, SalesOpportunity, SupportTicket, TicketComment, OnboardingTask
)

# Use get_user_model() instead of direct import
User = get_user_model()


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'tenant_type', 'status', 'is_active', 'plan_type', 'max_users', 'created_at']
    list_filter = ['tenant_type', 'status', 'is_active', 'plan_type', 'created_at']
    search_fields = ['name', 'subdomain', 'contact_email']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'subdomain', 'contact_email', 'phone', 'address')
        }),
        ('Lifecycle Management', {
            'fields': ('tenant_type', 'status', 'is_active', 'trial_start_date', 'trial_end_date')
        }),
        ('Subscription & Billing', {
            'fields': ('plan_type', 'max_users')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'hierarchy_level', 'is_system_role', 'created_at']
    list_filter = ['is_system_role', 'hierarchy_level']
    ordering = ['hierarchy_level']
    readonly_fields = ['created_at']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'codename', 'is_sensitive', 'created_at']
    list_filter = ['category', 'is_sensitive', 'created_at']
    search_fields = ['name', 'codename', 'description']
    readonly_fields = ['created_at']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'granted_at']
    list_filter = ['role', 'permission__category', 'granted_at']
    readonly_fields = ['granted_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'tenant', 'is_active', 'mfa_enabled', 'user_created_at']
    list_filter = ['is_active', 'role', 'tenant', 'mfa_enabled', 'has_financial_access', 'user_created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'user_created_at', 'user_updated_at', 'last_login_ip']
    
    # Override add_fieldsets to include role as required field
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('RBAC Information (Required)', {
            'fields': ('role', 'tenant', 'is_tenant_admin', 'has_financial_access')
        }),
        ('Security', {
            'fields': ('mfa_enabled',)
        }),
        ('Profile', {
            'fields': ('phone', 'user_timezone')
        }),
    )
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('RBAC Information', {
            'fields': ('tenant', 'role', 'is_tenant_admin', 'has_financial_access')
        }),
        ('Security', {
            'fields': ('mfa_enabled', 'backup_tokens', 'last_login_ip')
        }),
        ('Profile', {
            'fields': ('phone', 'user_timezone')
        }),
        ('Timestamps', {
            'fields': ('user_created_at', 'user_updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Override form to set role as required"""
        form = super().get_form(request, obj, **kwargs)
        if 'role' in form.base_fields:
            form.base_fields['role'].required = True
            # Set a sensible default role for new users
            if obj is None:  # Creating new user
                try:
                    from rbac.models import Role
                    default_role = Role.objects.filter(name='CLIENT_USER').first()
                    if default_role:
                        form.base_fields['role'].initial = default_role.id
                except:
                    pass
        return form


@admin.register(UserPermissionOverride)
class UserPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'is_granted', 'granted_by', 'created_at', 'expires_at']
    list_filter = ['is_granted', 'permission__category', 'created_at', 'expires_at']
    search_fields = ['user__username', 'permission__name', 'reason']
    readonly_fields = ['created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'tenant', 'ip_address', 'created_at']
    list_filter = ['action', 'resource_type', 'tenant', 'created_at']
    search_fields = ['user__username', 'resource_id', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted


# Admin/Support/Sales System Admin

@admin.register(AccountStatus)
class AccountStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'color_code', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(ClientAccount)
class ClientAccountAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'account_type', 'status', 'sales_rep', 'monthly_revenue', 'created_at']
    list_filter = ['account_type', 'status', 'sales_rep', 'created_at']
    search_fields = ['business_name', 'primary_contact__username', 'primary_contact__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('business_name', 'tenant', 'account_type', 'status', 'primary_contact')
        }),
        ('Contact Details', {
            'fields': ('phone', 'website')
        }),
        ('Sales Information', {
            'fields': ('sales_rep', 'monthly_revenue', 'annual_contract_value')
        }),
        ('Contract Dates', {
            'fields': ('trial_start_date', 'trial_end_date', 'contract_start_date', 'contract_end_date')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(SalesOpportunity)
class SalesOpportunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'client_account', 'stage', 'probability', 'estimated_value', 'expected_close_date', 'sales_rep']
    list_filter = ['stage', 'probability', 'tenant', 'sales_rep', 'expected_close_date', 'created_at']
    search_fields = ['name', 'tenant__name', 'client_account__business_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'expected_close_date'
    
    fieldsets = [
        ('Opportunity Details', {
            'fields': ('name', 'tenant', 'description')
        }),
        ('Optional Client Account Link', {
            'fields': ('client_account',),
            'description': 'Optional: Link to VacationDesktop internal account record for additional context'
        }),
        ('Stage & Probability', {
            'fields': ('stage', 'probability', 'estimated_value', 'expected_close_date')
        }),
        ('Assignment & Tracking', {
            'fields': ('sales_rep', 'last_activity_date', 'next_followup_date')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'subject', 'tenant', 'client_account', 'priority', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'category', 'tenant', 'assigned_to', 'created_at']
    search_fields = ['ticket_number', 'subject', 'description', 'tenant__name', 'client_account__business_name']
    readonly_fields = ['id', 'ticket_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [TicketCommentInline]
    
    fieldsets = [
        ('Ticket Information', {
            'fields': ('ticket_number', 'subject', 'description', 'tenant')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Optional Client Account Link', {
            'fields': ('client_account',),
            'description': 'Optional: Link to VacationDesktop internal account record for additional context'
        }),
        ('Resolution', {
            'fields': ('resolution', 'resolved_at', 'closed_at')
        }),
        ('SLA Tracking', {
            'fields': ('first_response_at', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['ticket__ticket_number', 'comment', 'author__username']
    readonly_fields = ['id', 'created_at']


@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'name', 'client_account', 'status', 'assigned_to', 'due_date', 'order']
    list_filter = ['status', 'tenant', 'assigned_to', 'due_date', 'created_at']
    search_fields = ['name', 'tenant__name', 'client_account__business_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['tenant', 'order']
    
    fieldsets = [
        ('Task Information', {
            'fields': ('tenant', 'name', 'description', 'order')
        }),
        ('Optional Client Account Link', {
            'fields': ('client_account',),
            'description': 'Optional: Link to VacationDesktop internal account record for additional context'
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at')
        }),
        ('Notes & Metadata', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
