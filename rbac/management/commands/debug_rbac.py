from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role, Permission, RolePermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug RBAC system - show roles, permissions, and assignments'

    def handle(self, *args, **options):
        self.stdout.write('=== RBAC DEBUG REPORT ===\n')
        
        # Check roles
        self.stdout.write('ROLES:')
        roles = Role.objects.all().order_by('hierarchy_level')
        for role in roles:
            self.stdout.write(f'  - {role.name}: {role.description} (Level {role.hierarchy_level})')
        
        # Check permissions
        self.stdout.write(f'\nPERMISSIONS:')
        permissions = Permission.objects.all().order_by('category', 'name')
        self.stdout.write(f'  Total permissions created: {permissions.count()}')
        
        by_category = {}
        for perm in permissions:
            if perm.category not in by_category:
                by_category[perm.category] = []
            by_category[perm.category].append(perm.name)
        
        for category, perms in by_category.items():
            self.stdout.write(f'  {category}: {len(perms)} permissions')
        
        # Check role permissions
        self.stdout.write(f'\nROLE PERMISSIONS:')
        for role in roles:
            role_perms = RolePermission.objects.filter(role=role)
            self.stdout.write(f'  {role.name}: {role_perms.count()} permissions assigned')
            
            if role.name == 'SUPER_ADMIN':
                self.stdout.write('    SUPER_ADMIN permissions:')
                for rp in role_perms[:10]:  # Show first 10
                    self.stdout.write(f'      - {rp.permission.name} ({rp.permission.category})')
                if role_perms.count() > 10:
                    self.stdout.write(f'      ... and {role_perms.count() - 10} more')
        
        # Check admin user
        self.stdout.write(f'\nADMIN USER:')
        try:
            admin = User.objects.get(username='admin')
            self.stdout.write(f'  Username: {admin.username}')
            self.stdout.write(f'  Role: {admin.role}')
            self.stdout.write(f'  Is superuser: {admin.is_superuser}')
            self.stdout.write(f'  Is staff: {admin.is_staff}')
            self.stdout.write(f'  Is active: {admin.is_active}')
            
            if admin.role:
                role_perms = RolePermission.objects.filter(role=admin.role).count()
                self.stdout.write(f'  Role permissions: {role_perms}')
            else:
                self.stdout.write('  ❌ No role assigned!')
                
        except User.DoesNotExist:
            self.stdout.write('  ❌ Admin user not found!')
        
        self.stdout.write('\n=== END RBAC DEBUG ===')