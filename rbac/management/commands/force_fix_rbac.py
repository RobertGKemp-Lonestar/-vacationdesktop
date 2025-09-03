from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rbac.models import Role, Permission, RolePermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Force fix RBAC permissions - ensure SUPER_ADMIN has all permissions'

    def handle(self, *args, **options):
        try:
            # Get SUPER_ADMIN role
            super_admin = Role.objects.get(name='SUPER_ADMIN')
            self.stdout.write(f'Found SUPER_ADMIN role: {super_admin}')
            
            # Get all permissions
            all_permissions = Permission.objects.all()
            self.stdout.write(f'Found {all_permissions.count()} total permissions')
            
            # Clear existing role permissions for SUPER_ADMIN (in case of duplicates)
            existing_count = RolePermission.objects.filter(role=super_admin).count()
            self.stdout.write(f'SUPER_ADMIN currently has {existing_count} permissions')
            
            # Add all permissions to SUPER_ADMIN
            created_count = 0
            for permission in all_permissions:
                role_perm, created = RolePermission.objects.get_or_create(
                    role=super_admin,
                    permission=permission
                )
                if created:
                    created_count += 1
            
            # Final count
            final_count = RolePermission.objects.filter(role=super_admin).count()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ SUPER_ADMIN permissions fixed!')
            )
            self.stdout.write(f'Created {created_count} new permission assignments')
            self.stdout.write(f'SUPER_ADMIN now has {final_count} total permissions')
            
            # Also check admin user
            try:
                admin_user = User.objects.get(username='admin')
                self.stdout.write(f'Admin user role: {admin_user.role}')
                if admin_user.role and admin_user.role.name == 'SUPER_ADMIN':
                    self.stdout.write('✅ Admin user has correct role')
                else:
                    self.stdout.write('❌ Admin user role is incorrect')
            except User.DoesNotExist:
                self.stdout.write('❌ Admin user not found')
                
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ SUPER_ADMIN role not found - run setup_rbac first')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )