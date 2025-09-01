from django.core.management.base import BaseCommand
from rbac.models import Role, Permission, RolePermission


class Command(BaseCommand):
    help = 'Sets up initial RBAC roles and permissions for VacationDesktop'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up RBAC system...')
        
        # Create roles
        roles_data = [
            {
                'name': 'SUPER_ADMIN',
                'description': 'Full system access across all tenants and system functions',
                'hierarchy_level': 1,
                'is_system_role': True
            },
            {
                'name': 'SYSTEM_ADMIN',
                'description': 'System administration functions, tenant management',
                'hierarchy_level': 2,
                'is_system_role': True
            },
            {
                'name': 'HELPDESK_USER',
                'description': 'Customer support and help desk functions',
                'hierarchy_level': 3,
                'is_system_role': True
            },
            {
                'name': 'CLIENT_ADMIN',
                'description': 'Full access within tenant organization',
                'hierarchy_level': 4,
                'is_system_role': False
            },
            {
                'name': 'CLIENT_USER',
                'description': 'Standard user access within tenant (limited financial access)',
                'hierarchy_level': 5,
                'is_system_role': False
            }
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(f'Created role: {role.get_name_display()}')
            else:
                self.stdout.write(f'Role already exists: {role.get_name_display()}')
        
        # Create permissions
        permissions_data = [
            # User Management
            {'name': 'View Users', 'codename': 'view_users', 'category': 'USER_MANAGEMENT', 'description': 'View user accounts'},
            {'name': 'Create Users', 'codename': 'create_users', 'category': 'USER_MANAGEMENT', 'description': 'Create new user accounts'},
            {'name': 'Edit Users', 'codename': 'edit_users', 'category': 'USER_MANAGEMENT', 'description': 'Edit existing user accounts'},
            {'name': 'Delete Users', 'codename': 'delete_users', 'category': 'USER_MANAGEMENT', 'description': 'Delete user accounts'},
            {'name': 'Manage User Roles', 'codename': 'manage_user_roles', 'category': 'USER_MANAGEMENT', 'description': 'Assign and modify user roles'},
            
            # Tenant Management
            {'name': 'View Tenants', 'codename': 'view_tenants', 'category': 'TENANT_MANAGEMENT', 'description': 'View tenant organizations'},
            {'name': 'Create Tenants', 'codename': 'create_tenants', 'category': 'TENANT_MANAGEMENT', 'description': 'Create new tenant organizations'},
            {'name': 'Edit Tenants', 'codename': 'edit_tenants', 'category': 'TENANT_MANAGEMENT', 'description': 'Edit tenant organizations'},
            {'name': 'Delete Tenants', 'codename': 'delete_tenants', 'category': 'TENANT_MANAGEMENT', 'description': 'Delete tenant organizations'},
            
            # CRM
            {'name': 'View CRM', 'codename': 'view_crm', 'category': 'CRM', 'description': 'View customer relationship data'},
            {'name': 'Create CRM Contacts', 'codename': 'create_crm_contacts', 'category': 'CRM', 'description': 'Create new CRM contacts'},
            {'name': 'Edit CRM Contacts', 'codename': 'edit_crm_contacts', 'category': 'CRM', 'description': 'Edit CRM contacts'},
            {'name': 'Delete CRM Contacts', 'codename': 'delete_crm_contacts', 'category': 'CRM', 'description': 'Delete CRM contacts'},
            
            # Supplier Management
            {'name': 'View Suppliers', 'codename': 'view_suppliers', 'category': 'SUPPLIER', 'description': 'View supplier/vendor information'},
            {'name': 'Create Suppliers', 'codename': 'create_suppliers', 'category': 'SUPPLIER', 'description': 'Add new suppliers/vendors'},
            {'name': 'Edit Suppliers', 'codename': 'edit_suppliers', 'category': 'SUPPLIER', 'description': 'Edit supplier/vendor information'},
            {'name': 'Delete Suppliers', 'codename': 'delete_suppliers', 'category': 'SUPPLIER', 'description': 'Delete suppliers/vendors'},
            
            # Forms Hub
            {'name': 'View Forms', 'codename': 'view_forms', 'category': 'FORMS', 'description': 'View custom forms'},
            {'name': 'Create Forms', 'codename': 'create_forms', 'category': 'FORMS', 'description': 'Create custom forms'},
            {'name': 'Edit Forms', 'codename': 'edit_forms', 'category': 'FORMS', 'description': 'Edit custom forms'},
            {'name': 'Delete Forms', 'codename': 'delete_forms', 'category': 'FORMS', 'description': 'Delete custom forms'},
            
            # Email Marketing
            {'name': 'View Email Campaigns', 'codename': 'view_email_campaigns', 'category': 'EMAIL_MARKETING', 'description': 'View email marketing campaigns'},
            {'name': 'Create Email Campaigns', 'codename': 'create_email_campaigns', 'category': 'EMAIL_MARKETING', 'description': 'Create email marketing campaigns'},
            {'name': 'Send Email Campaigns', 'codename': 'send_email_campaigns', 'category': 'EMAIL_MARKETING', 'description': 'Send email marketing campaigns'},
            {'name': 'Edit Email Campaigns', 'codename': 'edit_email_campaigns', 'category': 'EMAIL_MARKETING', 'description': 'Edit email marketing campaigns'},
            
            # Trip Builder
            {'name': 'View Trips', 'codename': 'view_trips', 'category': 'TRIP_BUILDER', 'description': 'View trip itineraries'},
            {'name': 'Create Trips', 'codename': 'create_trips', 'category': 'TRIP_BUILDER', 'description': 'Create trip itineraries'},
            {'name': 'Edit Trips', 'codename': 'edit_trips', 'category': 'TRIP_BUILDER', 'description': 'Edit trip itineraries'},
            {'name': 'Delete Trips', 'codename': 'delete_trips', 'category': 'TRIP_BUILDER', 'description': 'Delete trip itineraries'},
            
            # Invoice System
            {'name': 'View Invoices', 'codename': 'view_invoices', 'category': 'INVOICE', 'description': 'View invoices'},
            {'name': 'Create Invoices', 'codename': 'create_invoices', 'category': 'INVOICE', 'description': 'Create invoices'},
            {'name': 'Edit Invoices', 'codename': 'edit_invoices', 'category': 'INVOICE', 'description': 'Edit invoices'},
            {'name': 'Send Invoices', 'codename': 'send_invoices', 'category': 'INVOICE', 'description': 'Send invoices to customers'},
            
            # Payment System
            {'name': 'View Payments', 'codename': 'view_payments', 'category': 'PAYMENT', 'description': 'View payment records'},
            {'name': 'Process Payments', 'codename': 'process_payments', 'category': 'PAYMENT', 'description': 'Process customer payments'},
            {'name': 'Refund Payments', 'codename': 'refund_payments', 'category': 'PAYMENT', 'description': 'Process payment refunds'},
            
            # Financial Data - Sensitive
            {'name': 'View Financial Data', 'codename': 'view_financial_data', 'category': 'FINANCIAL', 'description': 'View financial reports and data', 'is_sensitive': True},
            {'name': 'Edit Financial Data', 'codename': 'edit_financial_data', 'category': 'FINANCIAL', 'description': 'Edit financial data', 'is_sensitive': True},
            
            # Destination Hub
            {'name': 'View Destinations', 'codename': 'view_destinations', 'category': 'DESTINATION', 'description': 'View destination information'},
            {'name': 'Edit Destinations', 'codename': 'edit_destinations', 'category': 'DESTINATION', 'description': 'Edit destination information'},
            
            # Tour Hub
            {'name': 'View Tours', 'codename': 'view_tours', 'category': 'TOUR', 'description': 'View tour itineraries'},
            {'name': 'Create Tours', 'codename': 'create_tours', 'category': 'TOUR', 'description': 'Create tour itineraries'},
            {'name': 'Edit Tours', 'codename': 'edit_tours', 'category': 'TOUR', 'description': 'Edit tour itineraries'},
            
            # Cruise Hub
            {'name': 'View Cruises', 'codename': 'view_cruises', 'category': 'CRUISE', 'description': 'View cruise itineraries'},
            {'name': 'Create Cruises', 'codename': 'create_cruises', 'category': 'CRUISE', 'description': 'Create cruise itineraries'},
            {'name': 'Edit Cruises', 'codename': 'edit_cruises', 'category': 'CRUISE', 'description': 'Edit cruise itineraries'},
            
            # Network Portal
            {'name': 'View Network', 'codename': 'view_network', 'category': 'NETWORK', 'description': 'View network portal'},
            {'name': 'Post to Network', 'codename': 'post_to_network', 'category': 'NETWORK', 'description': 'Post group space to network'},
            
            # Admin/Support/Sales System
            {'name': 'View Client Accounts', 'codename': 'view_client_accounts', 'category': 'ADMIN_SYSTEM', 'description': 'View client account information'},
            {'name': 'Create Client Accounts', 'codename': 'create_client_accounts', 'category': 'ADMIN_SYSTEM', 'description': 'Create new client accounts'},
            {'name': 'Edit Client Accounts', 'codename': 'edit_client_accounts', 'category': 'ADMIN_SYSTEM', 'description': 'Edit client account information'},
            {'name': 'Delete Client Accounts', 'codename': 'delete_client_accounts', 'category': 'ADMIN_SYSTEM', 'description': 'Delete client accounts'},
            
            # Support System
            {'name': 'View Support Tickets', 'codename': 'view_support_tickets', 'category': 'SUPPORT', 'description': 'View support tickets'},
            {'name': 'Create Support Tickets', 'codename': 'create_support_tickets', 'category': 'SUPPORT', 'description': 'Create new support tickets'},
            {'name': 'Edit Support Tickets', 'codename': 'edit_support_tickets', 'category': 'SUPPORT', 'description': 'Edit support tickets'},
            {'name': 'Assign Support Tickets', 'codename': 'assign_support_tickets', 'category': 'SUPPORT', 'description': 'Assign tickets to support staff'},
            {'name': 'Resolve Support Tickets', 'codename': 'resolve_support_tickets', 'category': 'SUPPORT', 'description': 'Mark tickets as resolved'},
            
            # Sales System
            {'name': 'View Sales Opportunities', 'codename': 'view_sales_opportunities', 'category': 'SALES', 'description': 'View sales pipeline and opportunities'},
            {'name': 'Create Sales Opportunities', 'codename': 'create_sales_opportunities', 'category': 'SALES', 'description': 'Create new sales opportunities'},
            {'name': 'Edit Sales Opportunities', 'codename': 'edit_sales_opportunities', 'category': 'SALES', 'description': 'Edit sales opportunities'},
            {'name': 'Delete Sales Opportunities', 'codename': 'delete_sales_opportunities', 'category': 'SALES', 'description': 'Delete sales opportunities'},
            {'name': 'View Sales Reports', 'codename': 'view_sales_reports', 'category': 'SALES', 'description': 'View sales analytics and reports'},
            
            # Onboarding System
            {'name': 'View Onboarding Tasks', 'codename': 'view_onboarding_tasks', 'category': 'ONBOARDING', 'description': 'View client onboarding tasks'},
            {'name': 'Create Onboarding Tasks', 'codename': 'create_onboarding_tasks', 'category': 'ONBOARDING', 'description': 'Create onboarding task templates'},
            {'name': 'Edit Onboarding Tasks', 'codename': 'edit_onboarding_tasks', 'category': 'ONBOARDING', 'description': 'Edit onboarding tasks'},
            {'name': 'Complete Onboarding Tasks', 'codename': 'complete_onboarding_tasks', 'category': 'ONBOARDING', 'description': 'Mark onboarding tasks as complete'},
            
            # Reports
            {'name': 'View Reports', 'codename': 'view_reports', 'category': 'REPORTS', 'description': 'View analytics and reports'},
            {'name': 'Create Reports', 'codename': 'create_reports', 'category': 'REPORTS', 'description': 'Create custom reports'},
        ]
        
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            if created:
                self.stdout.write(f'Created permission: {permission.name}')
            else:
                self.stdout.write(f'Permission already exists: {permission.name}')
        
        # Assign permissions to roles
        self._assign_permissions_to_roles()
        
        self.stdout.write(self.style.SUCCESS('RBAC setup completed successfully!'))
    
    def _assign_permissions_to_roles(self):
        """Assign permissions to roles based on hierarchy"""
        
        # Super Admin gets ALL permissions
        super_admin = Role.objects.get(name='SUPER_ADMIN')
        all_permissions = Permission.objects.all()
        for permission in all_permissions:
            RolePermission.objects.get_or_create(
                role=super_admin,
                permission=permission
            )
        self.stdout.write('Assigned all permissions to Super Admin')
        
        # System Admin - all system management + admin/support/sales functions
        system_admin = Role.objects.get(name='SYSTEM_ADMIN')
        system_admin_perms = Permission.objects.filter(
            category__in=['RBAC', 'AUDIT', 'USER_MANAGEMENT', 'TENANT_MANAGEMENT', 'ADMIN_SYSTEM', 'SUPPORT', 'SALES', 'ONBOARDING', 'REPORTS']
        )
        for permission in system_admin_perms:
            RolePermission.objects.get_or_create(
                role=system_admin,
                permission=permission
            )
        self.stdout.write('Assigned permissions to System Admin')
        
        # Help Desk User - support ticket management + view permissions
        helpdesk = Role.objects.get(name='HELPDESK_USER')
        
        # All view permissions (except financial)
        helpdesk_view_perms = Permission.objects.filter(
            codename__startswith='view_'
        ).exclude(
            category='FINANCIAL'  # No financial access
        )
        
        # Support ticket management permissions
        helpdesk_support_perms = Permission.objects.filter(
            category='SUPPORT'
        )
        
        # Combine permissions
        helpdesk_perms = helpdesk_view_perms.union(helpdesk_support_perms)
        
        for permission in helpdesk_perms:
            RolePermission.objects.get_or_create(
                role=helpdesk,
                permission=permission
            )
        self.stdout.write('Assigned permissions to Help Desk User')
        
        # Client Admin - all client-facing permissions
        client_admin = Role.objects.get(name='CLIENT_ADMIN')
        client_admin_perms = Permission.objects.exclude(
            category__in=['TENANT_MANAGEMENT']  # Cannot manage tenants
        )
        for permission in client_admin_perms:
            RolePermission.objects.get_or_create(
                role=client_admin,
                permission=permission
            )
        self.stdout.write('Assigned permissions to Client Admin')
        
        # Client User - standard permissions, no financial by default
        client_user = Role.objects.get(name='CLIENT_USER')
        client_user_perms = Permission.objects.exclude(
            category__in=['TENANT_MANAGEMENT', 'USER_MANAGEMENT', 'FINANCIAL']
        ).exclude(
            codename__in=['delete_crm_contacts', 'delete_suppliers', 'delete_forms', 
                         'delete_trips', 'refund_payments', 'create_reports']
        )
        for permission in client_user_perms:
            RolePermission.objects.get_or_create(
                role=client_user,
                permission=permission
            )
        self.stdout.write('Assigned permissions to Client User')