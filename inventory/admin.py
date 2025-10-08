from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserLinks, UserAccess, AuditLog


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
