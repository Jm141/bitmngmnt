"""
Unit tests for inventory management system
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import (
    User, UserLinks, UserAccess, AuditLog, AttendanceRecord, ShiftSchedule,
    Supplier, Item, StockLot, StockMovement, Recipe, RecipeItem,
    PurchaseOrder, PurchaseOrderItem
)
from .services import InventoryService, RecipeService, PurchaseOrderService
from django.core.exceptions import ValidationError


User = get_user_model()


class UserModelTestCase(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123',
            role='super_admin',
            first_name='Super',
            last_name='Admin'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            role='staff',
            first_name='Staff',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation"""
        self.assertEqual(self.super_admin.username, 'superadmin')
        self.assertEqual(self.super_admin.role, 'super_admin')
        self.assertTrue(self.super_admin.is_active)
    
    def test_user_has_admin_access(self):
        """Test has_admin_access method"""
        self.assertTrue(self.super_admin.has_admin_access())
        self.assertTrue(self.admin.has_admin_access())
        self.assertFalse(self.staff.has_admin_access())
    
    def test_user_can_manage_users(self):
        """Test can_manage_users method"""
        self.assertTrue(self.super_admin.can_manage_users())
        self.assertTrue(self.admin.can_manage_users())
        self.assertFalse(self.staff.can_manage_users())
    
    def test_user_can_give_admin_access(self):
        """Test can_give_admin_access method"""
        self.assertTrue(self.super_admin.can_give_admin_access())
        self.assertFalse(self.admin.can_give_admin_access())
        self.assertFalse(self.staff.can_give_admin_access())
    
    def test_user_age_calculation(self):
        """Test age calculation"""
        birthday = date(1990, 1, 1)
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            birthday=birthday
        )
        age = user.get_age()
        self.assertIsNotNone(age)
        self.assertGreater(age, 0)
    
    def test_user_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.super_admin), 'superadmin (Super Admin)')


class SupplierModelTestCase(TestCase):
    """Test cases for Supplier model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            phone='1234567890',
            email='supplier@test.com',
            address='123 Test St',
            created_by=self.user
        )
    
    def test_supplier_creation(self):
        """Test supplier creation"""
        self.assertEqual(self.supplier.name, 'Test Supplier')
        self.assertEqual(self.supplier.contact_person, 'John Doe')
        self.assertTrue(self.supplier.is_active)
    
    def test_supplier_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.supplier), 'Test Supplier')


class ItemModelTestCase(TestCase):
    """Test cases for Item model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg',
            description='Test description',
            reorder_level=10,
            min_order_qty=5,
            is_perishable=True,
            shelf_life_days=30,
            created_by=self.user
        )
    
    def test_item_creation(self):
        """Test item creation"""
        self.assertEqual(self.item.code, 'TEST001')
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.category, 'ingredient')
        self.assertTrue(self.item.is_perishable)
    
    def test_item_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.item), 'TEST001 - Test Item')
    
    def test_get_current_stock(self):
        """Test get_current_stock method"""
        # Initially should be 0
        self.assertEqual(self.item.get_current_stock(), 0)
        
        # Add stock lot
        StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            created_by=self.user
        )
        
        self.assertEqual(self.item.get_current_stock(), 100)
    
    def test_is_low_stock(self):
        """Test is_low_stock method"""
        # No stock, should be low
        self.assertTrue(self.item.is_low_stock())
        
        # Add stock below reorder level
        StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=5,
            unit='kg',
            created_by=self.user
        )
        self.assertTrue(self.item.is_low_stock())
        
        # Add more stock above reorder level
        StockLot.objects.create(
            item=self.item,
            lot_no='LOT002',
            qty=20,
            unit='kg',
            created_by=self.user
        )
        self.assertFalse(self.item.is_low_stock())


class StockLotModelTestCase(TestCase):
    """Test cases for StockLot model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            created_by=self.user
        )
        
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg',
            is_perishable=True,
            shelf_life_days=30,
            created_by=self.user
        )
        
        self.lot = StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=10),
            unit_cost=10.50,
            supplier=self.supplier,
            created_by=self.user
        )
    
    def test_stock_lot_creation(self):
        """Test stock lot creation"""
        self.assertEqual(self.lot.lot_no, 'LOT001')
        self.assertEqual(self.lot.qty, 100)
        self.assertEqual(self.lot.unit_cost, 10.50)
    
    def test_is_expired(self):
        """Test is_expired method"""
        # Not expired
        self.assertFalse(self.lot.is_expired())
        
        # Create expired lot
        expired_lot = StockLot.objects.create(
            item=self.item,
            lot_no='LOT002',
            qty=50,
            unit='kg',
            expires_at=timezone.now().date() - timedelta(days=1),
            created_by=self.user
        )
        self.assertTrue(expired_lot.is_expired())
    
    def test_is_expiring_soon(self):
        """Test is_expiring_soon method"""
        # Expiring within 7 days
        expiring_lot = StockLot.objects.create(
            item=self.item,
            lot_no='LOT003',
            qty=50,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )
        self.assertTrue(expiring_lot.is_expiring_soon(days=7))
        self.assertFalse(expiring_lot.is_expiring_soon(days=3))


class StockMovementModelTestCase(TestCase):
    """Test cases for StockMovement model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        self.lot = StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            created_by=self.user
        )
    
    def test_stock_movement_creation(self):
        """Test stock movement creation"""
        movement = StockMovement.objects.create(
            item=self.item,
            lot=self.lot,
            movement_type='receive',
            qty=100,
            unit='kg',
            reason='Initial stock',
            created_by=self.user
        )
        
        self.assertEqual(movement.movement_type, 'receive')
        self.assertEqual(movement.qty, 100)
    
    def test_is_inbound(self):
        """Test is_inbound method"""
        receive_movement = StockMovement.objects.create(
            item=self.item,
            lot=self.lot,
            movement_type='receive',
            qty=100,
            unit='kg',
            created_by=self.user
        )
        self.assertTrue(receive_movement.is_inbound())
        
        consume_movement = StockMovement.objects.create(
            item=self.item,
            lot=self.lot,
            movement_type='consume',
            qty=10,
            unit='kg',
            created_by=self.user
        )
        self.assertFalse(consume_movement.is_inbound())
    
    def test_is_outbound(self):
        """Test is_outbound method"""
        consume_movement = StockMovement.objects.create(
            item=self.item,
            lot=self.lot,
            movement_type='consume',
            qty=10,
            unit='kg',
            created_by=self.user
        )
        self.assertTrue(consume_movement.is_outbound())


class RecipeModelTestCase(TestCase):
    """Test cases for Recipe model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.product = Item.objects.create(
            code='PROD001',
            name='Test Product',
            category='finished_good',
            unit='pcs',
            created_by=self.user
        )
        
        self.ingredient = Item.objects.create(
            code='ING001',
            name='Test Ingredient',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            product=self.product,
            yield_qty=10,
            yield_unit='pcs',
            description='Test recipe description',
            created_by=self.user
        )
    
    def test_recipe_creation(self):
        """Test recipe creation"""
        self.assertEqual(self.recipe.name, 'Test Recipe')
        self.assertEqual(self.recipe.product, self.product)
        self.assertEqual(self.recipe.yield_qty, 10)
    
    def test_recipe_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.recipe), 'Test Recipe - Test Product')


class RecipeItemModelTestCase(TestCase):
    """Test cases for RecipeItem model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.product = Item.objects.create(
            code='PROD001',
            name='Test Product',
            category='finished_good',
            unit='pcs',
            created_by=self.user
        )
        
        self.ingredient = Item.objects.create(
            code='ING001',
            name='Test Ingredient',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            product=self.product,
            yield_qty=10,
            yield_unit='pcs',
            created_by=self.user
        )
        
        self.recipe_item = RecipeItem.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            qty=5,
            unit='kg',
            loss_factor=10
        )
    
    def test_recipe_item_creation(self):
        """Test recipe item creation"""
        self.assertEqual(self.recipe_item.qty, 5)
        self.assertEqual(self.recipe_item.loss_factor, 10)
    
    def test_get_adjusted_qty(self):
        """Test get_adjusted_qty method"""
        # 5kg with 10% loss factor = 5 * 1.1 = 5.5kg
        adjusted_qty = self.recipe_item.get_adjusted_qty()
        self.assertEqual(adjusted_qty, 5.5)


class InventoryServiceTestCase(TestCase):
    """Test cases for InventoryService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            created_by=self.user
        )
        
        # Create perishable item
        self.perishable_item = Item.objects.create(
            code='PERISH001',
            name='Perishable Item',
            category='ingredient',
            unit='kg',
            is_perishable=True,
            shelf_life_days=30,
            reorder_level=10,
            created_by=self.user
        )
        
        # Create non-perishable item
        self.non_perishable_item = Item.objects.create(
            code='NONPERISH001',
            name='Non-Perishable Item',
            category='ingredient',
            unit='kg',
            is_perishable=False,
            reorder_level=10,
            created_by=self.user
        )
    
    def test_receive_stock(self):
        """Test receive_stock method"""
        lot = InventoryService.receive_stock(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            user=self.user,
            supplier=self.supplier,
            expires_at=timezone.now().date() + timedelta(days=30),
            unit_cost=10.50,
            ref_no='REF001'
        )
        
        self.assertEqual(lot.qty, 100)
        self.assertEqual(lot.unit_cost, 10.50)
        self.assertEqual(self.perishable_item.get_current_stock(), 100)
    
    def test_consume_stock(self):
        """Test consume_stock method"""
        # First receive stock
        lot = InventoryService.receive_stock(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            user=self.user
        )
        
        # Then consume
        InventoryService.consume_stock(
            item=self.perishable_item,
            qty=30,
            reason='Production',
            user=self.user
        )
        
        # Refresh from database
        lot.refresh_from_db()
        self.assertEqual(lot.qty, 70)
        self.assertEqual(self.perishable_item.get_current_stock(), 70)
    
    def test_consume_stock_insufficient(self):
        """Test consume_stock with insufficient stock"""
        # Receive only 50
        InventoryService.receive_stock(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=50,
            unit='kg',
            user=self.user
        )
        
        # Try to consume 100 - should raise error
        with self.assertRaises(ValueError):
            InventoryService.consume_stock(
                item=self.perishable_item,
                qty=100,
                reason='Production',
                user=self.user
            )
    
    def test_get_available_lots_fefo(self):
        """Test FEFO logic for perishable items"""
        # Create lots with different expiry dates
        lot1 = StockLot.objects.create(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        
        lot2 = StockLot.objects.create(
            item=self.perishable_item,
            lot_no='LOT002',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=10),
            created_by=self.user
        )
        
        lot3 = StockLot.objects.create(
            item=self.perishable_item,
            lot_no='LOT003',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=20),
            created_by=self.user
        )
        
        # Get available lots - should be ordered by expiry date
        lots = InventoryService.get_available_lots(self.perishable_item)
        lots_list = list(lots)
        
        # LOT002 expires first, then LOT003, then LOT001
        self.assertEqual(lots_list[0].lot_no, 'LOT002')
        self.assertEqual(lots_list[1].lot_no, 'LOT003')
        self.assertEqual(lots_list[2].lot_no, 'LOT001')
    
    def test_get_available_lots_fifo(self):
        """Test FIFO logic for non-perishable items"""
        # Create lots with different received dates (created at different times)
        lot1 = StockLot.objects.create(
            item=self.non_perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            created_by=self.user
        )
        
        lot2 = StockLot.objects.create(
            item=self.non_perishable_item,
            lot_no='LOT002',
            qty=100,
            unit='kg',
            created_by=self.user
        )
        
        # Get available lots - should be ordered by received date
        lots = InventoryService.get_available_lots(self.non_perishable_item)
        lots_list = list(lots)
        
        # LOT001 was received first
        self.assertEqual(lots_list[0].lot_no, 'LOT001')
        self.assertEqual(lots_list[1].lot_no, 'LOT002')
    
    def test_get_low_stock_items(self):
        """Test get_low_stock_items method"""
        # No stock - should be in low stock list
        low_stock = InventoryService.get_low_stock_items()
        item_codes = [item['item'].code for item in low_stock]
        self.assertIn('PERISH001', item_codes)
        
        # Add stock above reorder level
        InventoryService.receive_stock(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=20,
            unit='kg',
            user=self.user
        )
        
        # Should not be in low stock list anymore
        low_stock = InventoryService.get_low_stock_items()
        item_codes = [item['item'].code for item in low_stock]
        self.assertNotIn('PERISH001', item_codes)
    
    def test_get_expiring_items(self):
        """Test get_expiring_items method"""
        # Create expiring lot
        StockLot.objects.create(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )
        
        # Should be in expiring items (within 7 days)
        expiring = InventoryService.get_expiring_items(days=7)
        self.assertEqual(expiring.count(), 1)
        
        # Should not be in expiring items (within 3 days)
        expiring = InventoryService.get_expiring_items(days=3)
        self.assertEqual(expiring.count(), 0)
    
    def test_get_expired_items(self):
        """Test get_expired_items method"""
        # Create expired lot
        StockLot.objects.create(
            item=self.perishable_item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            expires_at=timezone.now().date() - timedelta(days=1),
            created_by=self.user
        )
        
        # Should be in expired items
        expired = InventoryService.get_expired_items()
        self.assertEqual(expired.count(), 1)


class AttendanceRecordTestCase(TestCase):
    """Test cases for AttendanceRecord model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_attendance_record_creation(self):
        """Test attendance record creation"""
        today = timezone.now().date()
        record = AttendanceRecord.objects.create(
            user=self.user,
            date=today,
            time_in_am=timezone.now(),
            time_out_am=timezone.now() + timedelta(hours=4)
        )
        
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.date, today)
        self.assertTrue(record.is_am_complete())
        self.assertFalse(record.is_pm_complete())


class ShiftScheduleTestCase(TestCase):
    """Test cases for ShiftSchedule model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_shift_schedule_creation(self):
        """Test shift schedule creation"""
        today = timezone.now().date()
        schedule = ShiftSchedule.objects.create(
            user=self.user,
            shift_type='AM',
            effective_from=today,
            effective_to=today + timedelta(days=30)
        )
        
        self.assertEqual(schedule.user, self.user)
        self.assertEqual(schedule.shift_type, 'AM')


class AuditLogTestCase(TestCase):
    """Test cases for AuditLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_audit_log_creation(self):
        """Test audit log creation"""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='create',
            target_model='Item',
            target_id='12345',
            description='Created new item',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.target_model, 'Item')


class SecurityTestCase(TestCase):
    """Test cases for security module"""
    
    def setUp(self):
        """Set up test data"""
        from .security import (
            validate_user_input, sanitize_input, check_user_permissions,
            can_manage_user, get_user_permissions
        )
        self.validate_user_input = validate_user_input
        self.sanitize_input = sanitize_input
        self.check_user_permissions = check_user_permissions
        self.can_manage_user = can_manage_user
        self.get_user_permissions = get_user_permissions
        
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123',
            role='super_admin'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            role='staff'
        )
    
    def test_validate_user_input_valid(self):
        """Test validate_user_input with valid data"""
        data = {
            'name': 'Test Item',
            'description': 'This is a test description'
        }
        is_valid, msg = self.validate_user_input(data)
        self.assertTrue(is_valid)
    
    def test_validate_user_input_sql_injection(self):
        """Test validate_user_input with SQL injection attempt"""
        data = {
            'name': "Test'; DROP TABLE users; --"
        }
        is_valid, msg = self.validate_user_input(data)
        self.assertFalse(is_valid)
    
    def test_validate_user_input_xss(self):
        """Test validate_user_input with XSS attempt"""
        data = {
            'name': '<script>alert("XSS")</script>'
        }
        is_valid, msg = self.validate_user_input(data)
        self.assertFalse(is_valid)
    
    def test_sanitize_input(self):
        """Test sanitize_input"""
        data = {
            'name': '  Test Item  ',
            'description': '  Description with spaces  '
        }
        sanitized = self.sanitize_input(data)
        self.assertEqual(sanitized['name'], 'Test Item')
        self.assertEqual(sanitized['description'], 'Description with spaces')
    
    def test_check_user_permissions_super_admin(self):
        """Test super admin has all permissions"""
        has_perm = self.check_user_permissions(self.super_admin, 'inventory_write')
        self.assertTrue(has_perm)
    
    def test_check_user_permissions_admin(self):
        """Test admin has all permissions"""
        has_perm = self.check_user_permissions(self.admin, 'inventory_write')
        self.assertTrue(has_perm)
    
    def test_check_user_permissions_staff(self):
        """Test staff has no permissions by default"""
        has_perm = self.check_user_permissions(self.staff, 'inventory_write')
        self.assertFalse(has_perm)
    
    def test_can_manage_user_super_admin(self):
        """Test super admin can manage everyone"""
        self.assertTrue(self.can_manage_user(self.super_admin, self.admin))
        self.assertTrue(self.can_manage_user(self.super_admin, self.staff))
    
    def test_can_manage_user_admin(self):
        """Test admin can manage staff only"""
        self.assertTrue(self.can_manage_user(self.admin, self.staff))
        self.assertFalse(self.can_manage_user(self.admin, self.super_admin))
        self.assertFalse(self.can_manage_user(self.admin, self.admin))
    
    def test_can_manage_user_staff(self):
        """Test staff cannot manage anyone"""
        self.assertFalse(self.can_manage_user(self.staff, self.staff))
        self.assertFalse(self.can_manage_user(self.staff, self.admin))
    
    def test_get_user_permissions(self):
        """Test get_user_permissions"""
        # Super admin should have all permissions
        super_admin_perms = self.get_user_permissions(self.super_admin)
        self.assertGreater(len(super_admin_perms), 0)
        
        # Admin should have most permissions
        admin_perms = self.get_user_permissions(self.admin)
        self.assertGreater(len(admin_perms), 0)
        
        # Staff should have no permissions by default
        staff_perms = self.get_user_permissions(self.staff)
        self.assertEqual(len(staff_perms), 0)


class RecipeServiceTestCase(TestCase):
    """Test cases for RecipeService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create product
        self.product = Item.objects.create(
            code='PROD001',
            name='Test Product',
            category='finished_good',
            unit='pcs',
            created_by=self.user
        )
        
        # Create ingredients
        self.ingredient1 = Item.objects.create(
            code='ING001',
            name='Ingredient 1',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        self.ingredient2 = Item.objects.create(
            code='ING002',
            name='Ingredient 2',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        # Create recipe
        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            product=self.product,
            yield_qty=10,
            yield_unit='pcs',
            created_by=self.user
        )
        
        # Add recipe items
        RecipeItem.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient1,
            qty=5,
            unit='kg',
            loss_factor=10
        )
        
        RecipeItem.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient2,
            qty=3,
            unit='kg',
            loss_factor=5
        )
    
    def test_validate_recipe_production_insufficient_stock(self):
        """Test validate_recipe_production with insufficient stock"""
        result = RecipeService.validate_recipe_production(self.recipe, production_qty=10)
        self.assertFalse(result['can_produce'])
        self.assertGreater(len(result['missing_ingredients']), 0)
    
    def test_validate_recipe_production_sufficient_stock(self):
        """Test validate_recipe_production with sufficient stock"""
        # Add stock for ingredients
        InventoryService.receive_stock(
            item=self.ingredient1,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            user=self.user
        )
        
        InventoryService.receive_stock(
            item=self.ingredient2,
            lot_no='LOT002',
            qty=100,
            unit='kg',
            user=self.user
        )
        
        result = RecipeService.validate_recipe_production(self.recipe, production_qty=10)
        self.assertTrue(result['can_produce'])
        self.assertEqual(len(result['missing_ingredients']), 0)


class ProductionWorkflowTestCase(TestCase):
    """Test cases for production workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create product
        self.product = Item.objects.create(
            code='PROD001',
            name='Test Product',
            category='finished_good',
            unit='pcs',
            created_by=self.user
        )
        
        # Create ingredient
        self.ingredient = Item.objects.create(
            code='ING001',
            name='Test Ingredient',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
        
        # Create recipe
        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            product=self.product,
            yield_qty=10,
            yield_unit='pcs',
            created_by=self.user
        )
        
        # Add recipe item
        RecipeItem.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            qty=5,
            unit='kg',
            loss_factor=0
        )
    
    def test_produce_stock_success(self):
        """Test successful stock production"""
        # Add ingredient stock
        InventoryService.receive_stock(
            item=self.ingredient,
            lot_no='ING-LOT001',
            qty=100,
            unit='kg',
            user=self.user
        )
        
        # Produce
        produced_lot = InventoryService.produce_stock(
            recipe=self.recipe,
            production_qty=10,
            lot_no='PROD-LOT001',
            user=self.user
        )
        
        # Check produced lot
        self.assertEqual(produced_lot.qty, 10)
        self.assertEqual(produced_lot.item, self.product)
        
        # Check ingredient was consumed
        self.ingredient.refresh_from_db()
        remaining_stock = self.ingredient.get_current_stock()
        self.assertEqual(remaining_stock, 95)  # 100 - 5 = 95
    
    def test_produce_stock_insufficient_ingredients(self):
        """Test production fails with insufficient ingredients"""
        # Add insufficient ingredient stock
        InventoryService.receive_stock(
            item=self.ingredient,
            lot_no='ING-LOT001',
            qty=2,  # Need 5, only have 2
            unit='kg',
            user=self.user
        )
        
        # Try to produce - should fail
        with self.assertRaises(ValueError):
            InventoryService.produce_stock(
                recipe=self.recipe,
                production_qty=10,
                lot_no='PROD-LOT001',
                user=self.user
            )


class UserAccessTestCase(TestCase):
    """Test cases for UserAccess model"""
    
    def setUp(self):
        """Set up test data"""
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123',
            role='super_admin'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            role='staff'
        )
    
    def test_user_access_creation(self):
        """Test user access creation"""
        access = UserAccess.objects.create(
            user=self.staff,
            permission_type='inventory_read',
            granted_by=self.admin
        )
        
        self.assertEqual(access.user, self.staff)
        self.assertEqual(access.permission_type, 'inventory_read')
        self.assertTrue(access.is_active)
    
    def test_user_access_expiration(self):
        """Test user access expiration"""
        # Create access with expiry in the past
        access = UserAccess.objects.create(
            user=self.staff,
            permission_type='inventory_read',
            granted_by=self.admin,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.assertTrue(access.is_expired())
        
        # Create access with expiry in the future
        access2 = UserAccess.objects.create(
            user=self.staff,
            permission_type='inventory_write',
            granted_by=self.admin,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        self.assertFalse(access2.is_expired())


class UserLinksTestCase(TestCase):
    """Test cases for UserLinks model"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_user_link_creation(self):
        """Test user link creation"""
        link = UserLinks.objects.create(
            user=self.user1,
            linked_user=self.user2,
            link_type='manager'
        )
        
        self.assertEqual(link.user, self.user1)
        self.assertEqual(link.linked_user, self.user2)
        self.assertEqual(link.link_type, 'manager')
        self.assertTrue(link.is_active)


class StockAdjustmentTestCase(TestCase):
    """Test cases for stock adjustment"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg',
            created_by=self.user
        )
    
    def test_adjust_stock_positive(self):
        """Test positive stock adjustment"""
        # Adjust stock up
        InventoryService.adjust_stock(
            item=self.item,
            qty=50,
            reason='Inventory correction',
            user=self.user
        )
        
        # Check stock increased
        self.assertEqual(self.item.get_current_stock(), 50)
    
    def test_adjust_stock_negative(self):
        """Test negative stock adjustment"""
        # First add stock
        InventoryService.receive_stock(
            item=self.item,
            lot_no='LOT001',
            qty=100,
            unit='kg',
            user=self.user
        )
        
        # Adjust stock down
        InventoryService.adjust_stock(
            item=self.item,
            qty=-20,
            reason='Damaged goods',
            user=self.user
        )
        
        # Check stock decreased
        self.assertEqual(self.item.get_current_stock(), 80)


class MultiLotConsumptionTestCase(TestCase):
    """Test cases for multi-lot consumption"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg',
            is_perishable=True,
            shelf_life_days=30,
            created_by=self.user
        )
    
    def test_consume_from_multiple_lots(self):
        """Test consuming from multiple lots using FEFO"""
        # Create 3 lots with different expiry dates
        lot1 = StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=50,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        
        lot2 = StockLot.objects.create(
            item=self.item,
            lot_no='LOT002',
            qty=50,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=10),
            created_by=self.user
        )
        
        lot3 = StockLot.objects.create(
            item=self.item,
            lot_no='LOT003',
            qty=50,
            unit='kg',
            expires_at=timezone.now().date() + timedelta(days=20),
            created_by=self.user
        )
        
        # Consume 120 kg (should use lot2 completely, lot3 completely, and 20 from lot1)
        InventoryService.consume_stock(
            item=self.item,
            qty=120,
            reason='Production',
            user=self.user
        )
        
        # Check lots
        lot1.refresh_from_db()
        lot2.refresh_from_db()
        lot3.refresh_from_db()
        
        # LOT002 should be fully consumed (expires first)
        self.assertEqual(lot2.qty, 0)
        
        # LOT003 should be fully consumed (expires second)
        self.assertEqual(lot3.qty, 0)
        
        # LOT001 should have 30 remaining (50 - 20)
        self.assertEqual(lot1.qty, 30)

