from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


# Custom Manager for User model with security features
class UserManager(BaseUserManager):
    """
    Custom manager for User model
    """
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)
    
    def get_user_by_username_safe(self, username):
        """
        Safely get user by username using Django ORM (prevents SQL injection)
        """
        try:
            return self.get(username=username)
        except User.DoesNotExist:
            return None
    
    def get_users_by_role_safe(self, role):
        """
        Safely get users by role using Django ORM
        """
        return self.filter(role=role, is_active=True)
    
    def search_users_safe(self, search_term):
        """
        Safely search users using Django ORM
        """
        return self.filter(
            models.Q(username__icontains=search_term) |
            models.Q(first_name__icontains=search_term) |
            models.Q(last_name__icontains=search_term) |
            models.Q(email__icontains=search_term)
        ).filter(is_active=True)


class User(AbstractUser):
    """
    Extended User model with additional fields for inventory management
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('supplier', 'Supplier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    
    # Supplier-specific fields
    supplier = models.OneToOneField('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_account', help_text="Link to supplier if this is a supplier account")
    
    objects = UserManager()
    
    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def clean(self):
        super().clean()
        # Validate role hierarchy
        if self.role == 'super_admin' and self.created_by and self.created_by.role != 'super_admin':
            raise ValidationError("Only Super Admin can create Super Admin users.")
    
    def save(self, *args, **kwargs):
        validate = kwargs.pop('validate', True)
        if validate:
            self.full_clean()
        super().save(*args, **kwargs)
    
    def has_admin_access(self):
        """Check if user has admin or super admin access"""
        return self.role in ['admin', 'super_admin']
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['admin', 'super_admin']
    
    def can_give_admin_access(self):
        """Check if user can give admin access (only super admin)"""
        return self.role == 'super_admin'
    
    def is_supplier_user(self):
        """Check if user is a supplier account"""
        return self.role == 'supplier' and self.supplier is not None
    
    def get_supplier_orders(self):
        """Get purchase orders for this supplier user"""
        if self.is_supplier_user():
            return PurchaseOrder.objects.filter(supplier=self.supplier).order_by('-created_at')
        return PurchaseOrder.objects.none()
    
    def get_age(self):
        """Calculate age from birthday"""
        if not self.birthday:
            return None
        
        today = timezone.now().date()
        age = today.year - self.birthday.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.birthday.month or (today.month == self.birthday.month and today.day < self.birthday.day):
            age -= 1
        
        return age
    
    @property
    def age(self):
        """Property to get age"""
        return self.get_age()


class UserLinks(models.Model):
    """
    Model to store user relationships and access links
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_links')
    linked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='linked_by_users')
    link_type = models.CharField(max_length=50, choices=[
        ('manager', 'Manager'),
        ('subordinate', 'Subordinate'),
        ('colleague', 'Colleague'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_links'
        unique_together = ['user', 'linked_user', 'link_type']
        verbose_name = 'User Link'
        verbose_name_plural = 'User Links'
    
    def __str__(self):
        return f"{self.user.username} -> {self.linked_user.username} ({self.link_type})"


class UserAccess(models.Model):
    """
    Model to manage user permissions and access control
    """
    PERMISSION_TYPES = [
        ('inventory_read', 'Read Inventory'),
        ('inventory_write', 'Write Inventory'),
        ('inventory_delete', 'Delete Inventory'),
        ('user_read', 'Read Users'),
        ('user_write', 'Write Users'),
        ('user_delete', 'Delete Users'),
        ('reports_read', 'Read Reports'),
        ('reports_write', 'Write Reports'),
        ('settings_read', 'Read Settings'),
        ('settings_write', 'Write Settings'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_accesses')
    permission_type = models.CharField(max_length=50, choices=PERMISSION_TYPES)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_access'
        unique_together = ['user', 'permission_type']
        verbose_name = 'User Access'
        verbose_name_plural = 'User Accesses'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_type_display()}"
    
    def clean(self):
        super().clean()
        # Validate permission granting authority
        if self.granted_by.role not in ['admin', 'super_admin']:
            raise ValidationError("Only Admin or Super Admin can grant permissions.")
        
        # Super admin permissions can only be granted by super admin
        if self.permission_type in ['user_write', 'user_delete'] and self.granted_by.role != 'super_admin':
            raise ValidationError("Only Super Admin can grant user management permissions.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if permission has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class AuditLog(models.Model):
    """
    Model to track all user actions for security and compliance
    """
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_grant', 'Permission Grant'),
        ('permission_revoke', 'Permission Revoke'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.get_action_type_display()} - {self.timestamp}"


# --- Attendance / DTR ---
class ShiftSchedule(models.Model):
    """Schedule assignment for users (future-ready)."""
    SHIFT_CHOICES = [
        ('AM', 'Morning Shift'),
        ('PM', 'Afternoon Shift'),
        ('FULL', 'Whole Day'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shift_schedules')
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='FULL')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shift_schedule'
        verbose_name = 'Shift Schedule'
        verbose_name_plural = 'Shift Schedules'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.user.username} - {self.get_shift_type_display()}"


class AttendanceRecord(models.Model):
    """Daily attendance with AM/PM clock-ins/outs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time_in_am = models.DateTimeField(null=True, blank=True)
    time_out_am = models.DateTimeField(null=True, blank=True)
    time_in_pm = models.DateTimeField(null=True, blank=True)
    time_out_pm = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_record'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['user', 'date']
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def is_am_complete(self) -> bool:
        return bool(self.time_in_am and self.time_out_am)

    def is_pm_complete(self) -> bool:
        return bool(self.time_in_pm and self.time_out_pm)


# --- INVENTORY MANAGEMENT MODELS ---

class Supplier(models.Model):
    """
    Supplier master data
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_suppliers')

    class Meta:
        db_table = 'supplier'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Item master (ingredients/products): code, name, category, unit, reorder_level, min_order_qty, is_perishable, shelf_life_days
    """
    CATEGORY_CHOICES = [
        ('ingredient', 'Ingredient'),
        ('finished_good', 'Finished Good'),
        ('packaging', 'Packaging Material'),
        ('equipment', 'Equipment'),
    ]
    
    UNIT_CHOICES = [
        ('pcs', 'Pieces'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('L', 'Liter'),
        ('mL', 'Milliliter'),
        ('pack', 'Pack'),
        ('box', 'Box'),
        ('dozen', 'Dozen'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Stock management
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_order_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Perishable management
    is_perishable = models.BooleanField(default=False)
    shelf_life_days = models.PositiveIntegerField(default=0, help_text="Shelf life in days (0 for non-perishable)")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_items')

    class Meta:
        db_table = 'item'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @staticmethod
    def generate_item_code():
        """Generate item code in format YYYYMM0001"""
        from django.utils import timezone
        now = timezone.now()
        prefix = now.strftime('%Y%m')  # e.g., 202510 for October 2025
        
        # Get the last item code with this prefix
        last_item = Item.objects.filter(code__startswith=prefix).order_by('code').last()
        
        if last_item:
            # Extract the numeric part and increment
            last_number = int(last_item.code[-4:])
            new_number = last_number + 1
        else:
            # First item of the month
            new_number = 1
        
        # Format: YYYYMM0001
        return f"{prefix}{new_number:04d}"
    
    def save(self, *args, **kwargs):
        # Auto-generate code if not provided (new item)
        if not self.code:
            self.code = self.generate_item_code()
        super().save(*args, **kwargs)

    def get_current_stock(self):
        """Get current total stock quantity"""
        from django.db.models import Sum
        total = StockLot.objects.filter(item=self, qty__gt=0).aggregate(
            total=Sum('qty')
        )['total'] or 0
        return total

    def is_low_stock(self):
        """Check if item is below reorder level"""
        return self.get_current_stock() <= self.reorder_level

    def get_expiring_soon(self, days=7):
        """Get lots expiring within specified days"""
        from django.utils import timezone
        from datetime import timedelta
        expiry_date = timezone.now().date() + timedelta(days=days)
        return StockLot.objects.filter(
            item=self,
            qty__gt=0,
            expires_at__lte=expiry_date,
            expires_at__isnull=False
        )


class StockLot(models.Model):
    """
    StockLot model: item, lot_no, qty, unit, received_at, expires_at, unit_cost
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_lots')
    lot_no = models.CharField(max_length=100)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Item.UNIT_CHOICES)
    received_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_lots')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_stock_lots')

    class Meta:
        db_table = 'stock_lot'
        verbose_name = 'Stock Lot'
        verbose_name_plural = 'Stock Lots'
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.item.code} - Lot {self.lot_no} ({self.qty} {self.unit})"

    def is_expired(self):
        """Check if lot is expired"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.expires_at

    def is_expiring_soon(self, days=7):
        """Check if lot is expiring within specified days"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        from datetime import timedelta
        expiry_threshold = timezone.now().date() + timedelta(days=days)
        return self.expires_at <= expiry_threshold


class StockMovement(models.Model):
    """
    StockMovement model: item, lot(optional), type(receive/consume/produce/adjust), qty, unit, ref_no, reason, notes, created_by, timestamp
    """
    MOVEMENT_TYPES = [
        ('receive', 'Receive Stock'),
        ('consume', 'Consume Stock'),
        ('produce', 'Produce Stock'),
        ('adjust', 'Adjust Stock'),
        ('transfer', 'Transfer Stock'),
        ('spoilage', 'Spoilage'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_movements')
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Item.UNIT_CHOICES)
    ref_no = models.CharField(max_length=100, blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_movements')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movement'
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.code} ({self.qty} {self.unit})"

    def is_inbound(self):
        """Check if movement increases stock"""
        return self.movement_type in ['receive', 'produce', 'adjust']

    def is_outbound(self):
        """Check if movement decreases stock"""
        return self.movement_type in ['consume', 'spoilage', 'transfer']


class Recipe(models.Model):
    """
    Recipe model (product, yield_qty, unit)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    product = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='recipes', limit_choices_to={'category': 'finished_good'})
    yield_qty = models.DecimalField(max_digits=10, decimal_places=2)
    yield_unit = models.CharField(max_length=10, choices=Item.UNIT_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_recipes')

    class Meta:
        db_table = 'recipe'
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.product.name}"

    def get_total_cost(self):
        """Calculate total cost of recipe ingredients"""
        total_cost = 0
        for item in self.recipe_items.all():
            # Get current average cost of ingredient
            ingredient_cost = item.ingredient.get_current_stock() * item.ingredient.unit_cost if hasattr(item.ingredient, 'unit_cost') else 0
            total_cost += float(item.qty) * float(ingredient_cost)
        return total_cost


class RecipeItem(models.Model):
    """
    RecipeItem (ingredient, qty, unit, loss_factor%)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_items')
    ingredient = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='recipe_ingredients', limit_choices_to={'category': 'ingredient'})
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Item.UNIT_CHOICES)
    loss_factor = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Loss factor percentage (0-100)")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'recipe_item'
        verbose_name = 'Recipe Item'
        verbose_name_plural = 'Recipe Items'
        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name} ({self.qty} {self.unit})"

    def get_adjusted_qty(self):
        """Get quantity adjusted for loss factor"""
        loss_multiplier = 1 + (float(self.loss_factor) / 100)
        return float(self.qty) * loss_multiplier


# --- PURCHASE ORDER MODELS ---

class PurchaseOrder(models.Model):
    """
    Purchase Order model for supplier pre-orders with QR code tracking
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved by Supplier'),
        ('shipped', 'Shipped'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_no = models.CharField(max_length=100, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    qr_code = models.CharField(max_length=255, unique=True, blank=True, help_text="Unique QR code for order tracking")
    
    # Order details
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True, help_text="Set by supplier during approval")
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Supplier response
    supplier_notes = models.TextField(blank=True, null=True, help_text="Notes from supplier")
    approved_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # Internal tracking
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_purchase_orders')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchase_order'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PO-{self.order_no} - {self.supplier.name} ({self.get_status_display()})"
    
    @staticmethod
    def generate_order_no():
        """Generate unique order number in format PO-YYYYMMDD-XXXX"""
        from django.utils import timezone
        now = timezone.now()
        prefix = f"PO-{now.strftime('%Y%m%d')}"
        
        # Get the last order with this prefix
        last_order = PurchaseOrder.objects.filter(order_no__startswith=prefix).order_by('order_no').last()
        
        if last_order:
            # Extract the numeric part and increment
            last_number = int(last_order.order_no.split('-')[-1])
            new_number = last_number + 1
        else:
            # First order of the day
            new_number = 1
        
        return f"{prefix}-{new_number:04d}"
    
    def generate_qr_code(self):
        """Generate unique QR code for order tracking"""
        import hashlib
        import time
        
        # Create unique string from order details
        unique_string = f"{self.id}-{self.order_no}-{time.time()}"
        qr_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
        
        return f"PO-{qr_hash.upper()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate order number if not provided
        if not self.order_no:
            self.order_no = self.generate_order_no()
        
        # Auto-generate QR code if not provided
        if not self.qr_code:
            self.qr_code = self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate total order amount"""
        total = sum(item.subtotal() for item in self.order_items.all())
        return total
    
    def can_be_approved(self):
        """Check if order can be approved"""
        return self.status in ['draft', 'pending']
    
    def can_be_shipped(self):
        """Check if order can be marked as shipped"""
        return self.status == 'approved'
    
    def can_be_received(self):
        """Check if order can be received"""
        return self.status == 'shipped'
    
    def approve_order(self, supplier_notes=None, expected_delivery_date=None):
        """Approve order (supplier action)"""
        if not self.can_be_approved():
            raise ValueError("Order cannot be approved in current status")
        
        self.status = 'approved'
        self.approved_at = timezone.now()
        if supplier_notes:
            self.supplier_notes = supplier_notes
        if expected_delivery_date:
            self.expected_delivery_date = expected_delivery_date
        self.save()
    
    def mark_shipped(self):
        """Mark order as shipped"""
        if not self.can_be_shipped():
            raise ValueError("Order cannot be shipped in current status")
        
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        self.save()
    
    def mark_received(self, user):
        """Mark order as received"""
        if not self.can_be_received():
            raise ValueError("Order cannot be received in current status")
        
        self.status = 'received'
        self.received_at = timezone.now()
        self.actual_delivery_date = timezone.now().date()
        self.received_by = user
        self.save()


class PurchaseOrderItem(models.Model):
    """
    Purchase Order Item - individual items in a purchase order
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='purchase_order_items')
    qty_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Item.UNIT_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price set by supplier during approval")
    qty_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchase_order_item'
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        unique_together = ['purchase_order', 'item']
    
    def __str__(self):
        return f"{self.purchase_order.order_no} - {self.item.name} ({self.qty_ordered} {self.unit})"
    
    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.qty_ordered * self.unit_price
    
    def is_fully_received(self):
        """Check if full quantity has been received"""
        return self.qty_received >= self.qty_ordered
    
    def remaining_qty(self):
        """Calculate remaining quantity to receive"""
        return self.qty_ordered - self.qty_received