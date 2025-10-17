"""
Management command to clear all inventory data while preserving user accounts
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import (
    AuditLog, AttendanceRecord, ShiftSchedule, StockMovement, 
    StockLot, RecipeItem, Recipe, Item, Supplier, UserAccess, UserLinks
)


class Command(BaseCommand):
    help = 'Clear all inventory data while preserving user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the deletion of all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  WARNING: This will delete ALL data except user accounts!\n'
                    'Run with --confirm flag to proceed: python manage.py clear_inventory_data --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\n🗑️  Starting data cleanup...\n'))

        try:
            with transaction.atomic():
                # Delete in order to respect foreign key constraints
                
                # 1. Delete audit logs
                audit_count = AuditLog.objects.all().count()
                AuditLog.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {audit_count} audit log entries'))

                # 2. Delete attendance records
                attendance_count = AttendanceRecord.objects.all().count()
                AttendanceRecord.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {attendance_count} attendance records'))

                # 3. Delete shift schedules
                shift_count = ShiftSchedule.objects.all().count()
                ShiftSchedule.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {shift_count} shift schedules'))

                # 4. Delete stock movements
                movement_count = StockMovement.objects.all().count()
                StockMovement.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {movement_count} stock movements'))

                # 5. Delete stock lots
                lot_count = StockLot.objects.all().count()
                StockLot.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {lot_count} stock lots'))

                # 6. Delete recipe items (must come before recipes)
                recipe_item_count = RecipeItem.objects.all().count()
                RecipeItem.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {recipe_item_count} recipe items'))

                # 7. Delete recipes
                recipe_count = Recipe.objects.all().count()
                Recipe.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {recipe_count} recipes'))

                # 8. Delete items
                item_count = Item.objects.all().count()
                Item.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {item_count} items'))

                # 9. Delete suppliers
                supplier_count = Supplier.objects.all().count()
                Supplier.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {supplier_count} suppliers'))

                # 10. Delete user access records
                access_count = UserAccess.objects.all().count()
                UserAccess.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {access_count} user access records'))

                # 11. Delete user links
                link_count = UserLinks.objects.all().count()
                UserLinks.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted {link_count} user links'))

                self.stdout.write(
                    self.style.SUCCESS(
                        '\n✅ Successfully cleared all inventory data!\n'
                        '👤 User accounts have been preserved.\n'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Error during cleanup: {str(e)}\n'
                    'All changes have been rolled back.\n'
                )
            )
            raise

