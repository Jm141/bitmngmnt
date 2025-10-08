from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial super admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the super admin (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email for the super admin (default: admin@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the super admin (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Super',
            help='First name for the super admin (default: Super)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name for the super admin (default: Admin)'
        )
        parser.add_argument(
            '--birthday',
            type=str,
            default='1990-01-01',
            help='Birthday for the super admin (default: 1990-01-01)'
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
                # Check if super admin already exists
                if User.objects.filter(role='super_admin').exists():
                    self.stdout.write(
                        self.style.WARNING('Super admin user already exists!')
                    )
                    return

                # Generate username from first and last name
                generated_username = f"{first_name.lower()}.{last_name.lower()}"
                
                # Check if username exists and add number if needed
                counter = 1
                while User.objects.filter(username=generated_username).exists():
                    generated_username = f"{first_name.lower()}.{last_name.lower()}{counter}"
                    counter += 1
                
                # Create super admin user
                user = User.objects.create_user(
                    username=generated_username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    birthday=birthday,
                    role='super_admin',
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created super admin user: {generated_username}'
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
                    self.style.WARNING(
                        'Please change the password after first login!'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating super admin: {str(e)}')
            )
