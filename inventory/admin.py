from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserLinks, UserAccess, AuditLog, Supplier, Item, StockLot, StockMovement, Recipe, RecipeItem, PurchaseOrder, PurchaseOrderItem


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin with security features and role management
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at', 'created_by')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
        ('Created by', {'fields': ('created_by',)}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make role field readonly for non-super-admin users
        """
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and request.user.role != 'super_admin':
            readonly_fields.append('role')
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        """
        Set created_by field when creating new user
        """
        if not change:  # Creating new user
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserLinks)
class UserLinksAdmin(admin.ModelAdmin):
    """
    Admin for User Links management
    """
    list_display = ('user', 'linked_user', 'link_type', 'is_active', 'created_at')
    list_filter = ('link_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'linked_user__username')
    ordering = ('-created_at',)


@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    """
    Admin for User Access permissions
    """
    list_display = ('user', 'permission_type', 'granted_by', 'is_active', 'granted_at', 'expires_at')
    list_filter = ('permission_type', 'is_active', 'granted_at')
    search_fields = ('user__username', 'granted_by__username')
    ordering = ('-granted_at',)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make certain fields readonly based on user role
        """
        readonly_fields = ['granted_at']
        if not request.user.is_superuser and request.user.role != 'super_admin':
            readonly_fields.extend(['user', 'permission_type', 'granted_by'])
        return readonly_fields


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin for Audit Logs (read-only)
    """
    list_display = ('user', 'action_type', 'target_model', 'ip_address', 'timestamp')
    list_filter = ('action_type', 'target_model', 'timestamp')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'action_type', 'target_model', 'target_id', 'description', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# --- INVENTORY ADMIN ---

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """
    Admin for Supplier management
    """
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'contact_person')}),
        ('Contact Information', {'fields': ('phone', 'email', 'address')}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new supplier
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin for Item management
    """
    list_display = ('code', 'name', 'category', 'unit', 'reorder_level', 'is_perishable', 'is_active', 'created_at')
    list_filter = ('category', 'is_perishable', 'is_active', 'created_at')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    
    fieldsets = (
        ('Basic Information', {'fields': ('code', 'name', 'category', 'unit', 'description')}),
        ('Stock Management', {'fields': ('reorder_level', 'min_order_qty')}),
        ('Perishable Settings', {'fields': ('is_perishable', 'shelf_life_days')}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new item
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockLot)
class StockLotAdmin(admin.ModelAdmin):
    """
    Admin for StockLot management
    """
    list_display = ('item', 'lot_no', 'qty', 'unit', 'supplier', 'expires_at', 'unit_cost', 'received_at')
    list_filter = ('item__category', 'supplier', 'expires_at', 'received_at')
    search_fields = ('item__code', 'item__name', 'lot_no', 'supplier__name')
    ordering = ('-received_at',)
    
    fieldsets = (
        ('Lot Information', {'fields': ('item', 'lot_no', 'qty', 'unit')}),
        ('Supplier & Cost', {'fields': ('supplier', 'unit_cost')}),
        ('Expiry', {'fields': ('expires_at',)}),
        ('Notes', {'fields': ('notes',)}),
        ('Metadata', {'fields': ('received_at', 'created_by')}),
    )
    
    readonly_fields = ('received_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new lot
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """
    Admin for StockMovement management (read-only)
    """
    list_display = ('item', 'movement_type', 'qty', 'unit', 'lot', 'reason', 'created_by', 'timestamp')
    list_filter = ('movement_type', 'timestamp', 'created_by')
    search_fields = ('item__code', 'item__name', 'reason', 'ref_no')
    ordering = ('-timestamp',)
    readonly_fields = ('item', 'lot', 'movement_type', 'qty', 'unit', 'ref_no', 'reason', 'notes', 'created_by', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class RecipeItemInline(admin.TabularInline):
    """
    Inline admin for RecipeItem
    """
    model = RecipeItem
    extra = 1
    fields = ('ingredient', 'qty', 'unit', 'loss_factor', 'notes')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Admin for Recipe management
    """
    list_display = ('name', 'product', 'yield_qty', 'yield_unit', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'product__code', 'product__name', 'description')
    ordering = ('name',)
    inlines = [RecipeItemInline]
    
    fieldsets = (
        ('Recipe Information', {'fields': ('name', 'product', 'yield_qty', 'yield_unit', 'description')}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new recipe
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecipeItem)
class RecipeItemAdmin(admin.ModelAdmin):
    """
    Admin for RecipeItem management
    """
    list_display = ('recipe', 'ingredient', 'qty', 'unit', 'loss_factor')
    list_filter = ('recipe', 'ingredient__category')
    search_fields = ('recipe__name', 'ingredient__code', 'ingredient__name')
    ordering = ('recipe', 'ingredient')
    
    fieldsets = (
        ('Recipe Item', {'fields': ('recipe', 'ingredient', 'qty', 'unit')}),
        ('Loss Factor', {'fields': ('loss_factor',)}),
        ('Notes', {'fields': ('notes',)}),
    )


# --- PURCHASE ORDER ADMIN ---

class PurchaseOrderItemInline(admin.TabularInline):
    """
    Inline admin for PurchaseOrderItem
    """
    model = PurchaseOrderItem
    extra = 1
    fields = ('item', 'qty_ordered', 'unit_price', 'qty_received', 'notes')
    readonly_fields = ('qty_received',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """
    Admin for Purchase Order management
    """
    list_display = ('order_no', 'supplier', 'status', 'total_amount', 'order_date', 'expected_delivery_date', 'created_by')
    list_filter = ('status', 'supplier', 'order_date', 'expected_delivery_date')
    search_fields = ('order_no', 'supplier__name', 'qr_code')
    ordering = ('-created_at',)
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Order Information', {'fields': ('order_no', 'supplier', 'status', 'qr_code')}),
        ('Dates', {'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date')}),
        ('Supplier Response', {'fields': ('supplier_notes', 'supplier_approved_at', 'supplier_approved_by')}),
        ('Admin Response', {'fields': ('admin_notes', 'admin_approved_at', 'admin_approved_by')}),
        ('Cancellation', {'fields': ('cancelled_at', 'cancelled_by', 'cancellation_reason')}),
        ('Shipping & Receiving', {'fields': ('shipped_at', 'received_at', 'received_by')}),
        ('Internal', {'fields': ('notes', 'total_amount')}),
        ('Metadata', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ('order_no', 'qr_code', 'order_date', 'supplier_approved_at', 'supplier_approved_by', 'admin_approved_at', 'admin_approved_by', 'cancelled_at', 'cancelled_by', 'shipped_at', 'received_at', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new purchase order
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    """
    Admin for PurchaseOrderItem management
    """
    list_display = ('purchase_order', 'item', 'qty_ordered', 'unit_price', 'qty_received', 'subtotal_display')
    list_filter = ('purchase_order__status', 'item__category')
    search_fields = ('purchase_order__order_no', 'item__code', 'item__name')
    ordering = ('-purchase_order__created_at', 'item')
    
    fieldsets = (
        ('Order', {'fields': ('purchase_order', 'item')}),
        ('Quantities', {'fields': ('qty_ordered', 'unit', 'qty_received')}),
        ('Pricing', {'fields': ('unit_price',)}),
        ('Notes', {'fields': ('notes',)}),
    )
    
    readonly_fields = ('qty_received',)
    
    def subtotal_display(self, obj):
        return f"₱{obj.subtotal():,.2f}"
    subtotal_display.short_description = 'Subtotal'
