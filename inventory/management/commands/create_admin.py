from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from inventory.models import UserAccess

User = get_user_model()


class Command(BaseCommand):
    help = 'Create admin user with inventory permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@bakery.com',
            help='Email for the admin (default: admin@bakery.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Bakery',
            help='First name for the admin (default: Bakery)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name for the admin (default: Admin)'
        )
        parser.add_argument(
            '--birthday',
            type=str,
            default='1990-01-01',
            help='Birthday for the admin (default: 1990-01-01)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        birthday = options['birthday']

        try:
            with transaction.atomic():
                # Check if admin already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Admin user "{username}" already exists!')
                    )
                    return

                # Create admin user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    birthday=birthday,
                    role='admin',
                    is_staff=True,
                    is_superuser=False,
                    is_active=True
                )

                # Create UserAccess permissions for inventory management
                inventory_permissions = [
                    'inventory_read',
                    'inventory_write', 
                    'inventory_delete',
                    'reports_read',
                    'reports_write',
                    'settings_read',
                    'settings_write'
                ]

                # Get or create a super admin to grant permissions
                super_admin = User.objects.filter(role='super_admin').first()
                if not super_admin:
                    # Create a temporary super admin for granting permissions
                    super_admin = User.objects.create_user(
                        username='system',
                        email='system@bakery.com',
                        password='temp_password',
                        first_name='System',
                        last_name='Admin',
                        birthday='1990-01-01',
                        role='super_admin',
                        is_staff=True,
                        is_superuser=True,
                        is_active=True
                    )

                for permission in inventory_permissions:
                    UserAccess.objects.create(
                        user=user,
                        permission_type=permission,
                        granted_by=super_admin,
                        is_active=True
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created admin user: {username}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Email: {email}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Password: {password}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Role: admin (has all inventory permissions)'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'Please change the password after first login!'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin: {str(e)}')
            )
