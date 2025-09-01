from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class Tenant(models.Model):
    """Multi-tenant organization model for Travel Advisors"""
    
    # Tenant lifecycle types
    TENANT_TYPES = [
        ('PROSPECT', 'Prospect'),
        ('TRIAL', 'Trial'),
        ('CLIENT', 'Paying Client'),
    ]
    
    # Tenant status options
    TENANT_STATUSES = [
        ('ACTIVE', 'Active'),
        ('TRIAL_EXPIRED', 'Trial Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING_SETUP', 'Pending Setup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    subdomain = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Lifecycle management
    tenant_type = models.CharField(max_length=20, choices=TENANT_TYPES, default='PROSPECT')
    status = models.CharField(max_length=20, choices=TENANT_STATUSES, default='PENDING_SETUP')
    trial_start_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Business information
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Subscription/billing
    plan_type = models.CharField(max_length=50, default='basic')
    max_users = models.PositiveIntegerField(default=5)
    
    class Meta:
        db_table = 'tenants'
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """Hierarchical role system"""
    ROLE_TYPES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('SYSTEM_ADMIN', 'System Admin'),
        ('HELPDESK_USER', 'Help Desk User'),
        ('CLIENT_ADMIN', 'Client Admin'),
        ('CLIENT_USER', 'Client User'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_TYPES, unique=True)
    description = models.TextField()
    hierarchy_level = models.PositiveIntegerField()  # Lower number = higher priority
    is_system_role = models.BooleanField(default=False)  # System vs Client role
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'roles'
        ordering = ['hierarchy_level']
    
    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    """Granular permission system"""
    PERMISSION_CATEGORIES = [
        ('USER_MANAGEMENT', 'User Management'),
        ('TENANT_MANAGEMENT', 'Tenant Management'),
        ('CRM', 'Customer Relationship Management'),
        ('SUPPLIER', 'Supplier Management'),
        ('FORMS', 'Forms Hub'),
        ('EMAIL_MARKETING', 'Email Marketing'),
        ('TRIP_BUILDER', 'Trip Builder'),
        ('INVOICE', 'Invoice System'),
        ('PAYMENT', 'Payment System'),
        ('DESTINATION', 'Destination Hub'),
        ('TOUR', 'Tour Hub'),
        ('CRUISE', 'Cruise Hub'),
        ('NETWORK', 'Network Portal'),
        ('FINANCIAL', 'Financial Data'),
        ('REPORTS', 'Reports & Analytics'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=PERMISSION_CATEGORIES)
    is_sensitive = models.BooleanField(default=False)  # For financial/sensitive permissions
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'permissions'
    
    def __str__(self):
        return f"{self.category}: {self.name}"


class RolePermission(models.Model):
    """Many-to-many relationship between roles and permissions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']


class User(AbstractUser):
    """Extended user model with tenant and role support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Multi-tenancy
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    
    # Role-based access
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users')
    
    # MFA settings
    mfa_enabled = models.BooleanField(default=False)
    backup_tokens = models.JSONField(default=list, blank=True)
    
    # Profile information
    phone = models.CharField(max_length=20, blank=True)
    user_timezone = models.CharField(max_length=50, default='UTC')
    
    # Account status
    is_tenant_admin = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    user_created_at = models.DateTimeField(default=timezone.now)
    user_updated_at = models.DateTimeField(auto_now=True)
    
    # Financial access (special permission for Client Users)
    has_financial_access = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.role.name})"
    
    def get_permissions(self):
        """Get all permissions for this user based on role"""
        return Permission.objects.filter(
            rolepermission__role=self.role
        ).distinct()
    
    def has_permission(self, permission_codename):
        """Check if user has specific permission"""
        return self.get_permissions().filter(
            codename=permission_codename
        ).exists()
    
    def is_system_user(self):
        """Check if user is a system user (not tenant-specific)"""
        return self.role.is_system_role
    
    def can_access_financial_data(self):
        """Special check for financial data access"""
        if self.role.name == 'CLIENT_USER':
            return self.has_financial_access
        return self.has_permission('view_financial_data')


class UserPermissionOverride(models.Model):
    """Individual permission overrides for specific users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_granted = models.BooleanField()  # True = grant, False = revoke
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_overrides')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_permission_overrides'
        unique_together = ['user', 'permission']


class AuditLog(models.Model):
    """Audit trail for security and compliance"""
    ACTION_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete Record'),
        ('PERMISSION_GRANT', 'Permission Granted'),
        ('PERMISSION_REVOKE', 'Permission Revoked'),
        ('ROLE_CHANGE', 'Role Changed'),
        ('MFA_ENABLE', 'MFA Enabled'),
        ('MFA_DISABLE', 'MFA Disabled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"


# Admin/Support/Sales System Models

class AccountStatus(models.Model):
    """Account status lookup for client accounts"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    color_code = models.CharField(max_length=7, default='#007bff')  # Hex color for UI
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'account_statuses'
        verbose_name_plural = 'Account Statuses'
    
    def __str__(self):
        return self.name


class ClientAccount(models.Model):
    """Client account management for VacationDesktop employees"""
    ACCOUNT_TYPES = [
        ('PROSPECT', 'Prospect'),
        ('TRIAL', 'Trial Account'),
        ('ACTIVE', 'Active Client'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='client_account')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='PROSPECT')
    status = models.ForeignKey(AccountStatus, on_delete=models.PROTECT)
    
    # Business Information
    business_name = models.CharField(max_length=200)
    primary_contact = models.ForeignKey(User, on_delete=models.PROTECT, related_name='primary_accounts')
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Sales Information
    sales_rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='assigned_accounts', limit_choices_to={'role__name__in': ['Super Admin', 'System Admin']})
    monthly_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_contract_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Dates
    trial_start_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_accounts')
    
    class Meta:
        db_table = 'client_accounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business_name} ({self.get_account_type_display()})"


class SalesOpportunity(models.Model):
    """Sales pipeline and opportunity management"""
    OPPORTUNITY_STAGES = [
        ('LEAD', 'Lead'),
        ('QUALIFIED', 'Qualified Lead'),
        ('PROPOSAL', 'Proposal Sent'),
        ('NEGOTIATION', 'In Negotiation'),
        ('CLOSED_WON', 'Closed Won'),
        ('CLOSED_LOST', 'Closed Lost'),
    ]
    
    PROBABILITY_CHOICES = [
        (10, '10% - Initial Contact'),
        (25, '25% - Qualified Lead'),
        (50, '50% - Proposal Sent'),
        (75, '75% - In Negotiation'),
        (90, '90% - Verbal Agreement'),
        (100, '100% - Closed Won'),
        (0, '0% - Closed Lost'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='opportunities')
    client_account = models.ForeignKey(ClientAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities',
                                     help_text='Optional: VacationDesktop internal account record')
    
    # Opportunity Details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=OPPORTUNITY_STAGES, default='LEAD')
    probability = models.IntegerField(choices=PROBABILITY_CHOICES, default=10)
    
    # Financial
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_close_date = models.DateField()
    
    # Assignment
    sales_rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='sales_opportunities')
    
    # Tracking
    last_activity_date = models.DateTimeField(default=timezone.now)
    next_followup_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_opportunities')
    
    class Meta:
        db_table = 'sales_opportunities'
        ordering = ['-created_at']
        verbose_name_plural = 'Sales Opportunities'
    
    def __str__(self):
        return f"{self.name} - {self.get_stage_display()}"


class SupportTicket(models.Model):
    """Support ticket system for client issues"""
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING', 'Pending Customer'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical Issue'),
        ('BILLING', 'Billing Question'),
        ('FEATURE', 'Feature Request'),
        ('BUG', 'Bug Report'),
        ('TRAINING', 'Training/How-to'),
        ('ACCOUNT', 'Account Management'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Ticket Details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    # Relationships
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='support_tickets')
    client_account = models.ForeignKey(ClientAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets', 
                                     help_text='Optional: VacationDesktop internal account record')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tickets',
                                  help_text='Staff member who created this ticket')
    created_for = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_for_me',
                                   limit_choices_to={'role__is_system_role': False},
                                   help_text='Client user this ticket was created for (receives notifications)')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='assigned_tickets', limit_choices_to={'role__name__in': ['SUPER_ADMIN', 'SYSTEM_ADMIN', 'HELPDESK_USER']})
    
    # Tracking
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA Tracking
    first_response_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate unique ticket number
            import random
            self.ticket_number = f"VD-{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number}: {self.subject}"


class TicketComment(models.Model):
    """Comments/notes on support tickets"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal notes vs customer-visible
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ticket_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.author}"


class OnboardingTask(models.Model):
    """Client onboarding workflow tasks"""
    TASK_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='onboarding_tasks')
    client_account = models.ForeignKey(ClientAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='onboarding_tasks',
                                     help_text='Optional: VacationDesktop internal account record')
    
    # Task Details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)  # Task sequence
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='PENDING')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='onboarding_tasks')
    
    # Dates
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'onboarding_tasks'
        ordering = ['tenant', 'order']
    
    def __str__(self):
        return f"{self.tenant.name}: {self.name}"
