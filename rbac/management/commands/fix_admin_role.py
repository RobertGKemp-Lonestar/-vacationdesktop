from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix admin user role to be SUPER_ADMIN'

    def handle(self, *args, **options):
        try:
            # Get the admin user
            admin_user = User.objects.get(username='admin')
            self.stdout.write(f"Found admin user: {admin_user.username}")
            self.stdout.write(f"Current role: {admin_user.role}")
            
            # Get the SUPER_ADMIN role
            super_admin_role = Role.objects.get(name='SUPER_ADMIN')
            self.stdout.write(f"Found SUPER_ADMIN role: {super_admin_role}")
            
            # Update the user's role
            admin_user.role = super_admin_role
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully updated admin role to SUPER_ADMIN')
            )
            self.stdout.write(f'Admin user role is now: {admin_user.role}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Admin user not found')
            )
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ SUPER_ADMIN role not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing admin role: {e}')
            )