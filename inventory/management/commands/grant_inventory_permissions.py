from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from inventory.models import UserAccess

User = get_user_model()


class Command(BaseCommand):
    help = 'Grant inventory permissions to existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to grant permissions to (if not provided, grants to all admin users)'
        )
        parser.add_argument(
            '--permissions',
            type=str,
            nargs='+',
            default=['inventory_read', 'inventory_write', 'inventory_delete'],
            help='Permissions to grant (default: inventory_read, inventory_write, inventory_delete)'
        )

    def handle(self, *args, **options):
        username = options['username']
        permissions = options['permissions']

        try:
            with transaction.atomic():
                if username:
                    # Grant permissions to specific user
                    try:
                        user = User.objects.get(username=username)
                        self.grant_permissions_to_user(user, permissions)
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'User "{username}" not found!')
                        )
                        return
                else:
                    # Grant permissions to all admin users
                    admin_users = User.objects.filter(role__in=['admin', 'super_admin'])
                    if not admin_users.exists():
                        self.stdout.write(
                            self.style.WARNING('No admin users found!')
                        )
                        return
                    
                    for user in admin_users:
                        self.grant_permissions_to_user(user, permissions)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error granting permissions: {str(e)}')
            )

    def grant_permissions_to_user(self, user, permissions):
        """Grant permissions to a specific user"""
        granted_count = 0
        
        # Get or create a super admin to grant permissions
        super_admin = User.objects.filter(role='super_admin').first()
        if not super_admin:
            # Create a temporary super admin for granting permissions
            super_admin = User.objects.create_user(
                username='system_grant',
                email='system@bakery.com',
                password='temp_password',
                first_name='System',
                last_name='Grant',
                birthday='1990-01-01',
                role='super_admin',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
        
        for permission in permissions:
            # Check if permission already exists
            if not UserAccess.objects.filter(
                user=user, 
                permission_type=permission
            ).exists():
                UserAccess.objects.create(
                    user=user,
                    permission_type=permission,
                    granted_by=super_admin,
                    is_active=True
                )
                granted_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Granted "{permission}" permission to {user.username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User {user.username} already has "{permission}" permission'
                    )
                )
        
        if granted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully granted {granted_count} permissions to {user.username}'
                )
            )
