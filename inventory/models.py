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