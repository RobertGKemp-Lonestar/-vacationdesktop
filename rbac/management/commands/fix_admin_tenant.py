from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix admin user tenant assignment - SUPER_ADMIN should have tenant=None'

    def handle(self, *args, **options):
        try:
            # Get the admin user
            admin_user = User.objects.get(username='admin')
            self.stdout.write(f"Found admin user: {admin_user.username}")
            self.stdout.write(f"Current role: {admin_user.role}")
            self.stdout.write(f"Current tenant: {admin_user.tenant}")
            
            # Check if user has SUPER_ADMIN role
            if admin_user.role and admin_user.role.name == 'SUPER_ADMIN':
                if admin_user.tenant is not None:
                    old_tenant = admin_user.tenant
                    admin_user.tenant = None
                    admin_user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Fixed admin tenant assignment!')
                    )
                    self.stdout.write(f'Changed from: {old_tenant}')
                    self.stdout.write(f'Changed to: None (system-wide access)')
                else:
                    self.stdout.write(f'✅ Admin user tenant is already correctly set to None')
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Admin user does not have SUPER_ADMIN role: {admin_user.role}')
                )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Admin user not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing admin tenant: {e}')
            )