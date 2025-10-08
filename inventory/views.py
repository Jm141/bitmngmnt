from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, UserLinks, UserAccess, AuditLog, AttendanceRecord, ShiftSchedule
from .security import (
    role_required, permission_required, super_admin_required, admin_required,
    log_user_action, validate_user_input, sanitize_input, can_manage_user,
    get_user_permissions, check_user_permissions
)
from .forms import UserForm, UserAccessForm, UserLinksForm
import json


@login_required
def dashboard(request):
    """
    Main dashboard view
    """
    # Staff users: redirect to attendance dashboard
    if request.user.role == 'staff':
        return redirect('inventory:attendance_dashboard')

    context = {
        'user': request.user,
        'permissions': get_user_permissions(request.user),
        'recent_activities': AuditLog.objects.filter(user=request.user)[:10],
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def attendance_dashboard(request):
    """Staff self-attendance view with today's record and calendar list."""
    if request.user.role not in ['staff', 'admin', 'super_admin']:
        messages.error(request, "Unauthorized")
        return redirect('inventory:dashboard')

    today = timezone.now().date()
    # Staff can only see their own; admin/super_admin can switch user via param later
    target_user = request.user
    records = AttendanceRecord.objects.filter(user=target_user).order_by('-date')[:30]
    try:
        record_today = AttendanceRecord.objects.get(user=target_user, date=today)
    except AttendanceRecord.DoesNotExist:
        record_today = None

    context = {
        'target_user': target_user,
        'records': records,
        'record_today': record_today,
        'now': timezone.now(),
    }
    return render(request, 'inventory/attendance_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def clock_event(request):
    """Clock in/out with AM/PM constraints; staff can only clock self."""
    if request.user.role not in ['staff', 'admin', 'super_admin']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    action = request.POST.get('action')  # time_in_am, time_out_am, time_in_pm, time_out_pm
    now_dt = timezone.now()
    today = now_dt.date()
    record, _ = AttendanceRecord.objects.get_or_create(user=request.user, date=today)

    # Enforce single set per AM/PM
    if action == 'time_in_am':
        if record.time_in_am:
            return JsonResponse({'error': 'AM time-in already recorded'}, status=400)
        record.time_in_am = now_dt
    elif action == 'time_out_am':
        if not record.time_in_am:
            return JsonResponse({'error': 'AM time-in required first'}, status=400)
        if record.time_out_am:
            return JsonResponse({'error': 'AM time-out already recorded'}, status=400)
        record.time_out_am = now_dt
    elif action == 'time_in_pm':
        if record.time_in_pm:
            return JsonResponse({'error': 'PM time-in already recorded'}, status=400)
        record.time_in_pm = now_dt
    elif action == 'time_out_pm':
        if not record.time_in_pm:
            return JsonResponse({'error': 'PM time-in required first'}, status=400)
        if record.time_out_pm:
            return JsonResponse({'error': 'PM time-out already recorded'}, status=400)
        record.time_out_pm = now_dt
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    record.save()
    log_user_action(
        user=request.user,
        action_type='update',
        target_model='AttendanceRecord',
        target_id=record.id,
        description=f"Clock event {action}",
        request=request
    )
    return JsonResponse({'success': True})


@login_required
@admin_required
def user_list(request):
    """
    List all users with pagination and search
    """
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Hide Super Admin accounts from the user list
    users = User.objects.exclude(role='super_admin')
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='User',
        description=f"Viewed user list with search: {search_query}",
        request=request
    )
    
    return render(request, 'inventory/user_list.html', context)


@login_required
@admin_required
def user_detail(request, user_id):
    """
    View user details
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if current user can view this user
    if not can_manage_user(request.user, user) and request.user != user:
        messages.error(request, "You don't have permission to view this user.")
        return redirect('user_list')
    
    user_accesses = UserAccess.objects.filter(user=user, is_active=True)
    user_links = UserLinks.objects.filter(user=user, is_active=True)
    
    context = {
        'target_user': user,
        'user_accesses': user_accesses,
        'user_links': user_links,
        'can_manage': can_manage_user(request.user, user),
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='User',
        target_id=user_id,
        description=f"Viewed user details for {user.username}",
        request=request
    )
    
    return render(request, 'inventory/user_detail.html', context)


@login_required
@admin_required
def user_create(request):
    """
    Create new user
    """
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # Validate input
            is_valid, error_msg = validate_user_input(form.cleaned_data)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, 'inventory/user_form.html', {'form': form})
            
            # Sanitize input
            cleaned_data = sanitize_input(form.cleaned_data)
            
            # Check role permissions
            role = cleaned_data.get('role', 'staff')
            if role == 'super_admin' and request.user.role != 'super_admin':
                messages.error(request, "Only Super Admin can create Super Admin users.")
                return render(request, 'inventory/user_form.html', {'form': form})
            
            if role == 'admin' and request.user.role not in ['admin', 'super_admin']:
                messages.error(request, "Only Admin or Super Admin can create Admin users.")
                return render(request, 'inventory/user_form.html', {'form': form})
            
            # Create user - let the form handle username generation and saving
            user = form.save(commit=False)
            user.created_by = request.user
            # Avoid double full_clean: form already validated; skip model.full_clean()
            user.save(validate=False)
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='User',
                target_id=user.id,
                description=f"Created user {user.username} with role {user.role}",
                request=request
            )
            
            messages.success(request, f"User {user.username} created successfully.")
            return redirect('inventory:user_detail', user_id=user.id)
    else:
        form = UserForm()
    
    context = {
        'form': form,
        'title': 'Create User',
        'can_create_admin': request.user.role == 'super_admin',
    }
    
    return render(request, 'inventory/user_form.html', context)


@login_required
@admin_required
def user_update(request, user_id):
    """
    Update user
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if current user can manage this user
    if not can_manage_user(request.user, user):
        messages.error(request, "You don't have permission to edit this user.")
        return redirect('user_list')
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            # Validate input
            is_valid, error_msg = validate_user_input(form.cleaned_data)
            if not is_valid:
                messages.error(request, error_msg)
                return render(request, 'inventory/user_form.html', {'form': form, 'user': user})
            
            # Sanitize input
            cleaned_data = sanitize_input(form.cleaned_data)
            
            # Check role change permissions
            new_role = cleaned_data.get('role')
            if new_role != user.role:
                if new_role == 'super_admin' and request.user.role != 'super_admin':
                    messages.error(request, "Only Super Admin can promote users to Super Admin.")
                    return render(request, 'inventory/user_form.html', {'form': form, 'user': user})
                
                if new_role == 'admin' and request.user.role not in ['admin', 'super_admin']:
                    messages.error(request, "Only Admin or Super Admin can promote users to Admin.")
                    return render(request, 'inventory/user_form.html', {'form': form, 'user': user})
            
            # Update user
            form.save()
            
            log_user_action(
                user=request.user,
                action_type='update',
                target_model='User',
                target_id=user_id,
                description=f"Updated user {user.username}",
                request=request
            )
            
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect('user_detail', user_id=user.id)
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Update User: {user.username}',
        'can_promote_admin': request.user.role == 'super_admin',
    }
    
    return render(request, 'inventory/user_form.html', context)


@login_required
@super_admin_required
def user_delete(request, user_id):
    """
    Delete user (only Super Admin)
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        
        log_user_action(
            user=request.user,
            action_type='delete',
            target_model='User',
            target_id=user_id,
            description=f"Deleted user {username}",
            request=request
        )
        
        messages.success(request, f"User {username} deleted successfully.")
        return redirect('user_list')
    
    context = {
        'user': user,
    }
    
    return render(request, 'inventory/user_confirm_delete.html', context)


@login_required
@admin_required
def user_permissions(request, user_id):
    """
    Manage user permissions
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if current user can manage this user
    if not can_manage_user(request.user, user):
        messages.error(request, "You don't have permission to manage this user.")
        return redirect('user_list')
    
    if request.method == 'POST':
        # Bulk update via checkboxes
        if request.POST.get('bulk_update') == '1':
            selected_permissions = set(request.POST.getlist('permissions'))
            restricted = {'user_write', 'user_delete'}
            if (selected_permissions & restricted) and request.user.role != 'super_admin':
                messages.error(request, "Only Super Admin can grant user management permissions.")
                return redirect('inventory:user_permissions', user_id=user_id)

            # Activate selected, deactivate others
            for perm_type, _ in UserAccess.PERMISSION_TYPES:
                if perm_type in selected_permissions:
                    UserAccess.objects.update_or_create(
                        user=user,
                        permission_type=perm_type,
                        defaults={'granted_by': request.user, 'is_active': True}
                    )
                else:
                    UserAccess.objects.filter(user=user, permission_type=perm_type).update(is_active=False)

            log_user_action(
                user=request.user,
                action_type='permission_grant',
                target_model='UserAccess',
                description=f"Bulk updated permissions for {user.username}",
                request=request
            )
            messages.success(request, f"Permissions updated for {user.username}.")
            return redirect('inventory:user_permissions', user_id=user_id)

        # Single grant/revoke fallback
        permission_type = request.POST.get('permission_type')
        action = request.POST.get('action')  # 'grant' or 'revoke'
        if action == 'grant':
            if permission_type in ['user_write', 'user_delete'] and request.user.role != 'super_admin':
                messages.error(request, "Only Super Admin can grant user management permissions.")
                return redirect('inventory:user_permissions', user_id=user_id)
            UserAccess.objects.update_or_create(
                user=user,
                permission_type=permission_type,
                defaults={'granted_by': request.user, 'is_active': True}
            )
            log_user_action(
                user=request.user,
                action_type='permission_grant',
                target_model='UserAccess',
                description=f"Granted {permission_type} permission to {user.username}",
                request=request
            )
            messages.success(request, f"Permission {permission_type} granted to {user.username}.")
        elif action == 'revoke':
            UserAccess.objects.filter(user=user, permission_type=permission_type).update(is_active=False)
            log_user_action(
                user=request.user,
                action_type='permission_revoke',
                target_model='UserAccess',
                description=f"Revoked {permission_type} permission from {user.username}",
                request=request
            )
            messages.success(request, f"Permission {permission_type} revoked from {user.username}.")
        return redirect('inventory:user_permissions', user_id=user_id)
    
    # Get current permissions
    current_permissions = UserAccess.objects.filter(user=user, is_active=True)
    available_permissions = UserAccess.PERMISSION_TYPES
    current_permission_types = set(current_permissions.values_list('permission_type', flat=True))
    
    context = {
        'user': user,
        'current_permissions': current_permissions,
        'available_permissions': available_permissions,
        'can_grant_admin_permissions': request.user.role == 'super_admin',
        'current_permission_types': current_permission_types,
    }
    
    return render(request, 'inventory/user_permissions.html', context)


@login_required
def audit_logs(request):
    """
    View audit logs
    """
    if not check_user_permissions(request.user, 'reports_read'):
        messages.error(request, "You don't have permission to view audit logs.")
        return redirect('dashboard')
    
    logs = AuditLog.objects.all()
    
    # Filter by user if specified
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    # Filter by action type
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)
    
    context = {
        'logs': logs,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'action_choices': AuditLog.ACTION_TYPES,
    }
    
    return render(request, 'inventory/audit_logs.html', context)


@csrf_protect
@require_http_methods(["POST"])
def user_toggle_status(request, user_id):
    """
    Toggle user active status
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if not check_user_permissions(request.user, 'user_write'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    if not can_manage_user(request.user, user):
        return JsonResponse({'error': 'Cannot manage this user'}, status=403)
    
    # Toggle status
    user.is_active = not user.is_active
    user.save()
    
    log_user_action(
        user=request.user,
        action_type='update',
        target_model='User',
        target_id=user_id,
        description=f"Toggled user status to {'active' if user.is_active else 'inactive'}",
        request=request
    )
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f"User {user.username} is now {'active' if user.is_active else 'inactive'}"
    })


@login_required
@admin_required
def admin_attendance_overview(request):
    """
    Admin view to see all staff attendance records
    """
    # Get date filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_filter = request.GET.get('user')
    
    # Get all staff users
    staff_users = User.objects.filter(role='staff', is_active=True).order_by('first_name', 'last_name')
    
    # Get attendance records
    attendance_records = AttendanceRecord.objects.select_related('user').all()
    
    # Apply filters
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__lte=date_to_obj)
        except ValueError:
            pass
    
    if user_filter:
        attendance_records = attendance_records.filter(user__id=user_filter)
    
    # Order by date (most recent first)
    attendance_records = attendance_records.order_by('-date', 'user__first_name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(attendance_records, 20)
    page_number = request.GET.get('page')
    attendance_records = paginator.get_page(page_number)
    
    # Get summary statistics
    total_records = AttendanceRecord.objects.count()
    today_records = AttendanceRecord.objects.filter(date=timezone.now().date()).count()
    active_staff = staff_users.count()
    
    context = {
        'attendance_records': attendance_records,
        'staff_users': staff_users,
        'date_from': date_from,
        'date_to': date_to,
        'user_filter': user_filter,
        'total_records': total_records,
        'today_records': today_records,
        'active_staff': active_staff,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='AttendanceRecord',
        description="Viewed admin attendance overview",
        request=request
    )
    
    return render(request, 'inventory/admin_attendance_overview.html', context)