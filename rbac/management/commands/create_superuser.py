from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role, Tenant

# Use get_user_model() instead of direct import
User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with proper RBAC configuration'
    
    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for superuser')
        parser.add_argument('--email', type=str, help='Email for superuser')
        parser.add_argument('--password', type=str, help='Password for superuser')
    
    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')
        
        # Get Super Admin role
        try:
            super_admin_role = Role.objects.get(name='SUPER_ADMIN')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Super Admin role not found. Run setup_rbac first.'))
            return
        
        # Create superuser
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User {username} already exists.'))
            return
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=super_admin_role,
            is_staff=True,
            is_superuser=True,
            tenant=None  # System users don't belong to a tenant
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser: {username} with Super Admin role')
        )