from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin user immediately'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'VacationAdmin2024!'
        email = 'admin@example.com'
        
        try:
            # Delete existing admin user
            User.objects.filter(username=username).delete()
            self.stdout.write("Deleted existing admin user")
            
            # Get the SUPER_ADMIN role (created by setup_rbac)
            try:
                role = Role.objects.get(name='SUPER_ADMIN')
                self.stdout.write("Found SUPER_ADMIN role")
            except Role.DoesNotExist:
                self.stdout.write("SUPER_ADMIN role not found - run setup_rbac first!")
                return
            
            # Create admin user with no tenant (system-wide access)
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator'
            )
            user.role = role
            user.tenant = None  # System users don't belong to a specific tenant
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS('✅ ADMIN USER CREATED SUCCESSFULLY!')
            )
            self.stdout.write(f'URL: https://web-production-c5d67.up.railway.app/login/')
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Email: {email}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create admin user: {e}')
            )
            raise