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
from .models import User, UserLinks, UserAccess, AuditLog, AttendanceRecord, ShiftSchedule, Supplier, Item, StockLot, StockMovement, Recipe, RecipeItem
from .security import (
    role_required, permission_required, super_admin_required, admin_required,
    log_user_action, validate_user_input, sanitize_input, can_manage_user,
    get_user_permissions, check_user_permissions
)
from .forms import UserForm, UserAccessForm, UserLinksForm, SupplierForm, ItemForm, StockLotForm, StockMovementForm, RecipeForm, RecipeItemForm, StockReceiveForm, StockConsumeForm, ProductionForm
from .services import InventoryService, RecipeService
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


# --- INVENTORY MANAGEMENT VIEWS ---

@login_required
@permission_required('inventory_read')
def inventory_dashboard(request):
    """
    Inventory dashboard with KPIs and alerts
    """
    # Get stock summary
    stock_summary = InventoryService.get_stock_summary()
    
    # Get low stock items
    low_stock_items = InventoryService.get_low_stock_items()
    
    # Get expiring items (next 7 days)
    expiring_items = InventoryService.get_expiring_items(days=7)
    
    # Get expired items
    expired_items = InventoryService.get_expired_items()
    
    # Recent movements
    recent_movements = StockMovement.objects.select_related('item', 'created_by').order_by('-timestamp')[:10]
    
    context = {
        'stock_summary': stock_summary,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'expired_items': expired_items,
        'recent_movements': recent_movements,
    }
    
    return render(request, 'inventory/inventory_dashboard.html', context)


@login_required
@permission_required('inventory_read')
def item_list(request):
    """
    List all items with search and filter
    """
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    items = Item.objects.all()
    
    # Apply search filter
    if search_query:
        items = items.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Add current stock information
    items_with_stock = []
    for item in items:
        current_stock = item.get_current_stock()
        items_with_stock.append({
            'item': item,
            'current_stock': current_stock,
            'is_low_stock': item.is_low_stock(),
            'expiring_soon': item.get_expiring_soon().count()
        })
    
    # Pagination
    paginator = Paginator(items_with_stock, 20)
    page_number = request.GET.get('page')
    items_with_stock = paginator.get_page(page_number)
    
    context = {
        'items_with_stock': items_with_stock,
        'search_query': search_query,
        'category_filter': category_filter,
        'category_choices': Item.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/item_list.html', context)


@login_required
@permission_required('inventory_read')
def item_detail(request, item_id):
    """
    View item details with stock lots and movements
    """
    item = get_object_or_404(Item, id=item_id)
    
    # Get stock lots
    stock_lots = StockLot.objects.filter(item=item).order_by('-received_at')
    
    # Get recent movements
    movements = StockMovement.objects.filter(item=item).order_by('-timestamp')[:20]
    
    # Get current stock
    current_stock = item.get_current_stock()
    
    # Get expiring lots
    expiring_lots = item.get_expiring_soon()
    
    context = {
        'item': item,
        'stock_lots': stock_lots,
        'movements': movements,
        'current_stock': current_stock,
        'expiring_lots': expiring_lots,
    }
    
    return render(request, 'inventory/item_detail.html', context)


@login_required
@permission_required('inventory_write')
def item_create(request):
    """
    Create new item
    """
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='Item',
                target_id=item.id,
                description=f"Created item {item.code} - {item.name}",
                request=request
            )
            
            messages.success(request, f"Item {item.code} created successfully.")
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = ItemForm()
    
    context = {
        'form': form,
        'title': 'Create Item',
    }
    
    return render(request, 'inventory/item_form.html', context)


@login_required
@permission_required('inventory_write')
def item_update(request, item_id):
    """
    Update item
    """
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            
            log_user_action(
                user=request.user,
                action_type='update',
                target_model='Item',
                target_id=item_id,
                description=f"Updated item {item.code}",
                request=request
            )
            
            messages.success(request, f"Item {item.code} updated successfully.")
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = ItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'title': f'Update Item: {item.code}',
    }
    
    return render(request, 'inventory/item_form.html', context)


@login_required
@permission_required('inventory_write')
def stock_receive(request):
    """
    Receive stock workflow
    """
    if request.method == 'POST':
        form = StockReceiveForm(request.POST)
        if form.is_valid():
            try:
                lot = InventoryService.receive_stock(
                    item=form.cleaned_data['item'],
                    lot_no=form.cleaned_data['lot_no'],
                    qty=form.cleaned_data['qty'],
                    unit=form.cleaned_data['unit'],
                    user=request.user,
                    supplier=form.cleaned_data.get('supplier'),
                    expires_at=form.cleaned_data.get('expires_at'),
                    unit_cost=form.cleaned_data['unit_cost'],
                    ref_no=form.cleaned_data.get('ref_no'),
                    notes=form.cleaned_data.get('notes')
                )
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='StockLot',
                    target_id=lot.id,
                    description=f"Received stock: {lot.item.code} - Lot {lot.lot_no}",
                    request=request
                )
                
                messages.success(request, f"Stock received successfully. Lot: {lot.lot_no}")
                return redirect('inventory:item_detail', item_id=lot.item.id)
                
            except Exception as e:
                messages.error(request, f"Error receiving stock: {str(e)}")
    else:
        form = StockReceiveForm()
    
    context = {
        'form': form,
        'title': 'Receive Stock',
    }
    
    return render(request, 'inventory/stock_receive.html', context)


@login_required
@permission_required('inventory_write')
def stock_consume(request):
    """
    Consume stock workflow
    """
    if request.method == 'POST':
        form = StockConsumeForm(request.POST)
        if form.is_valid():
            try:
                InventoryService.consume_stock(
                    item=form.cleaned_data['item'],
                    qty=form.cleaned_data['qty'],
                    reason=form.cleaned_data['reason'],
                    user=request.user,
                    lot=form.cleaned_data.get('lot'),
                    ref_no=form.cleaned_data.get('ref_no'),
                    notes=form.cleaned_data.get('notes')
                )
                
                log_user_action(
                    user=request.user,
                    action_type='update',
                    target_model='StockMovement',
                    description=f"Consumed stock: {form.cleaned_data['item'].code}",
                    request=request
                )
                
                messages.success(request, "Stock consumed successfully.")
                return redirect('inventory:item_detail', item_id=form.cleaned_data['item'].id)
                
            except Exception as e:
                messages.error(request, f"Error consuming stock: {str(e)}")
    else:
        form = StockConsumeForm()
    
    context = {
        'form': form,
        'title': 'Consume Stock',
    }
    
    return render(request, 'inventory/stock_consume.html', context)


@login_required
@permission_required('inventory_write')
def production_create(request):
    """
    Production workflow
    """
    if request.method == 'POST':
        form = ProductionForm(request.POST)
        if form.is_valid():
            try:
                recipe = form.cleaned_data['recipe']
                production_qty = form.cleaned_data['production_qty']
                
                # Validate production
                validation = RecipeService.validate_recipe_production(recipe, production_qty)
                
                if not validation['can_produce']:
                    messages.error(request, "Cannot produce due to insufficient ingredients:")
                    for missing in validation['missing_ingredients']:
                        messages.error(request, f"- {missing['ingredient'].name}: Need {missing['needed']}, Available {missing['available']}")
                    return render(request, 'inventory/production_form.html', {'form': form, 'title': 'Production'})
                
                # Proceed with production
                lot = InventoryService.produce_stock(
                    recipe=recipe,
                    production_qty=production_qty,
                    lot_no=form.cleaned_data['lot_no'],
                    user=request.user,
                    expires_at=form.cleaned_data.get('expires_at'),
                    notes=form.cleaned_data.get('notes')
                )
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='StockLot',
                    target_id=lot.id,
                    description=f"Produced: {recipe.product.code} - Lot {lot.lot_no}",
                    request=request
                )
                
                messages.success(request, f"Production completed successfully. Lot: {lot.lot_no}")
                return redirect('inventory:item_detail', item_id=recipe.product.id)
                
            except Exception as e:
                messages.error(request, f"Error in production: {str(e)}")
    else:
        form = ProductionForm()
    
    context = {
        'form': form,
        'title': 'Production',
    }
    
    return render(request, 'inventory/production_form.html', context)


@login_required
@permission_required('inventory_read')
def supplier_list(request):
    """
    List all suppliers
    """
    suppliers = Supplier.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers,
    }
    
    return render(request, 'inventory/supplier_list.html', context)


@login_required
@permission_required('inventory_write')
def supplier_create(request):
    """
    Create new supplier
    """
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='Supplier',
                target_id=supplier.id,
                description=f"Created supplier {supplier.name}",
                request=request
            )
            
            messages.success(request, f"Supplier {supplier.name} created successfully.")
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
        'title': 'Create Supplier',
    }
    
    return render(request, 'inventory/supplier_form.html', context)


@login_required
@permission_required('inventory_read')
def recipe_list(request):
    """
    List all recipes
    """
    recipes = Recipe.objects.filter(is_active=True).order_by('name')
    
    # Add cost information
    recipes_with_cost = []
    for recipe in recipes:
        total_cost = RecipeService.calculate_recipe_cost(recipe)
        recipes_with_cost.append({
            'recipe': recipe,
            'total_cost': total_cost,
            'cost_per_unit': total_cost / recipe.yield_qty if recipe.yield_qty > 0 else 0
        })
    
    # Pagination
    paginator = Paginator(recipes_with_cost, 20)
    page_number = request.GET.get('page')
    recipes_with_cost = paginator.get_page(page_number)
    
    context = {
        'recipes_with_cost': recipes_with_cost,
    }
    
    return render(request, 'inventory/recipe_list.html', context)


@login_required
@permission_required('inventory_read')
def recipe_detail(request, recipe_id):
    """
    View recipe details
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Get recipe items
    recipe_items = RecipeItem.objects.filter(recipe=recipe)
    
    # Calculate costs
    total_cost = RecipeService.calculate_recipe_cost(recipe)
    cost_per_unit = total_cost / recipe.yield_qty if recipe.yield_qty > 0 else 0
    
    context = {
        'recipe': recipe,
        'recipe_items': recipe_items,
        'total_cost': total_cost,
        'cost_per_unit': cost_per_unit,
    }
    
    return render(request, 'inventory/recipe_detail.html', context)


@login_required
@permission_required('inventory_write')
def recipe_create(request):
    """
    Create new recipe
    """
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='Recipe',
                target_id=recipe.id,
                description=f"Created recipe {recipe.name}",
                request=request
            )
            
            messages.success(request, f"Recipe {recipe.name} created successfully.")
            return redirect('inventory:recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm()
    
    context = {
        'form': form,
        'title': 'Create Recipe',
    }
    
    return render(request, 'inventory/recipe_form.html', context)


@login_required
@permission_required('reports_read')
def stock_report(request):
    """
    Stock report with filters
    """
    # Get filters
    category_filter = request.GET.get('category', '')
    low_stock_only = request.GET.get('low_stock', False)
    
    items = Item.objects.filter(is_active=True)
    
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Build report data
    report_data = []
    for item in items:
        current_stock = item.get_current_stock()
        is_low_stock = item.is_low_stock()
        
        if low_stock_only and not is_low_stock:
            continue
        
        report_data.append({
            'item': item,
            'current_stock': current_stock,
            'reorder_level': item.reorder_level,
            'is_low_stock': is_low_stock,
            'expiring_soon': item.get_expiring_soon().count(),
            'unit_cost': InventoryService.calculate_item_cost(item)
        })
    
    context = {
        'report_data': report_data,
        'category_filter': category_filter,
        'low_stock_only': low_stock_only,
        'category_choices': Item.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/stock_report.html', context)