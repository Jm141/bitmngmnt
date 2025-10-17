from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import View
from functools import wraps
import logging
from .models import User, UserAccess, AuditLog
from django.utils import timezone
try:
    # Prefer zoneinfo from stdlib (Python 3.9+)
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

logger = logging.getLogger(__name__)


def log_user_action(user, action_type, target_model, target_id=None, description="", request=None):
    """
    Log user actions for audit trail
    """
    try:
        AuditLog.objects.create(
            user=user,
            action_type=action_type,
            target_model=target_model,
            target_id=str(target_id) if target_id else None,
            description=description,
            ip_address=request.META.get('REMOTE_ADDR', 'Unknown') if request else 'Unknown',
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown') if request else 'Unknown'
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")


def role_required(allowed_roles):
    """
    Decorator to check user role
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_type):
    """
    Decorator to check specific permission
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Super admin and admin have all permissions
            if request.user.role in ['super_admin', 'admin']:
                return view_func(request, *args, **kwargs)
            
            # Check specific permission
            has_permission = UserAccess.objects.filter(
                user=request.user,
                permission_type=permission_type,
                is_active=True
            ).exists()
            
            if not has_permission:
                messages.error(request, f"You don't have permission to perform this action.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def super_admin_required(view_func):
    """
    Decorator to require super admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role != 'super_admin':
            messages.error(request, "Only Super Admin can access this page.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Decorator to require admin or super admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['admin', 'super_admin']:
            messages.error(request, "Only Admin or Super Admin can access this page.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def supplier_required(view_func):
    """
    Decorator to require supplier account access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('inventory:supplier_login')
        
        if not request.user.is_supplier_user():
            messages.error(request, "You don't have permission to access this page. Supplier access required.")
            return redirect('inventory:login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def supplier_or_admin_required(view_func):
    """
    Decorator to require supplier OR admin access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('inventory:login')
        
        if not (request.user.is_supplier_user() or request.user.role in ['admin', 'super_admin']):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('inventory:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class SecureViewMixin:
    """
    Mixin for secure views with CSRF protection and audit logging
    """
    
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Log view access
        log_user_action(
            user=request.user,
            action_type='read',
            target_model=self.__class__.__name__,
            description=f"Accessed {self.__class__.__name__}",
            request=request
        )
        return super().dispatch(request, *args, **kwargs)


def validate_user_input(data, required_fields=None):
    """
    Validate user input to prevent injection attacks
    """
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Field '{field}' is required"
    
    # Check for potential SQL injection patterns (more targeted)
    dangerous_patterns = [
        ('--;', 'SQL comment'),
        ('/*', 'SQL comment block'),
        ('*/', 'SQL comment block'),
        ('xp_', 'SQL extended procedure'),
        ('sp_', 'SQL stored procedure'),
        (' exec ', 'SQL execution'),
        (' execute ', 'SQL execution'),
        (' union ', 'SQL union'),
        (' select ', 'SQL select'),
        (' insert ', 'SQL insert'),
        (' update ', 'SQL update'),
        (' delete ', 'SQL delete'),
        (' drop ', 'SQL drop'),
        (' create ', 'SQL create'),
        (' alter ', 'SQL alter'),
        ('<script', 'XSS script tag'),
        ('javascript:', 'XSS javascript'),
        ('onerror=', 'XSS event handler'),
        ('onload=', 'XSS event handler'),
    ]
    
    for key, value in data.items():
        if isinstance(value, str):
            value_lower = value.lower()
            for pattern, description in dangerous_patterns:
                if pattern in value_lower:
                    return False, f"Invalid input detected in field '{key}': {description}"
    
    return True, "Valid input"


def sanitize_input(data):
    """
    Sanitize user input
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(data, str):
        return data.strip()
    return data


def get_client_ip(request):
    """
    Get client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_manila_now():
    """
    Return current timezone-aware datetime in Asia/Manila.
    Uses zoneinfo if available, otherwise falls back to Django timezone's now().
    """
    now = timezone.now()
    if ZoneInfo is not None:
        try:
            return now.astimezone(ZoneInfo('Asia/Manila'))
        except Exception:
            return now
    # Fallback: return Django-aware now (may use settings.TIME_ZONE)
    return now


def check_user_permissions(user, permission_type):
    """
    Check if user has specific permission
    """
    # Super admin and admin have all permissions
    if user.role in ['super_admin', 'admin']:
        return True
    
    # Check specific permission
    return UserAccess.objects.filter(
        user=user,
        permission_type=permission_type,
        is_active=True
    ).exists()


def can_manage_user(current_user, target_user):
    """
    Check if current user can manage target user
    """
    # Super admin can manage everyone
    if current_user.role == 'super_admin':
        return True
    
    # Admin can manage staff but not other admins or super admins
    if current_user.role == 'admin':
        return target_user.role == 'staff'
    
    # Staff cannot manage anyone
    return False


def get_user_permissions(user):
    """
    Get all permissions for a user
    """
    permissions = []
    
    # Super admin has all permissions
    if user.role == 'super_admin':
        permissions = [choice[0] for choice in UserAccess.PERMISSION_TYPES]
    # Admin has most permissions except user management
    elif user.role == 'admin':
        permissions = [choice[0] for choice in UserAccess.PERMISSION_TYPES 
                      if choice[0] not in ['user_write', 'user_delete']]
    else:
        # Staff permissions from UserAccess
        user_accesses = UserAccess.objects.filter(user=user, is_active=True)
        permissions = [access.permission_type for access in user_accesses]
    
    return permissions
