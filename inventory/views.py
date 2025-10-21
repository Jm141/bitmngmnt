from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import pytz
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, UserLinks, UserAccess, AuditLog, AttendanceRecord, ShiftSchedule, Supplier, Item, StockLot, StockMovement, Recipe, RecipeItem, PurchaseOrder, PurchaseOrderItem
from .security import (
    role_required, permission_required, super_admin_required, admin_required,
    log_user_action, validate_user_input, sanitize_input, can_manage_user,
    get_user_permissions, check_user_permissions, get_manila_now,
    supplier_required, supplier_or_admin_required
)
from .forms import UserForm, UserAccessForm, UserLinksForm, SupplierForm, ItemForm, StockLotForm, StockMovementForm, RecipeForm, RecipeItemForm, StockReceiveForm, StockConsumeForm, ProductionForm, PurchaseOrderForm, PurchaseOrderItemForm, PurchaseOrderApproveForm, QRCodeScanForm
from .services import InventoryService, RecipeService, PurchaseOrderService
import json
from django.http import HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal


def unified_login(request):
    """
    Unified login view for all user types - redirects based on role
    """
    if request.user.is_authenticated:
        # Redirect authenticated users based on their role
        if request.user.is_supplier_user():
            return redirect('inventory:supplier_dashboard')
        elif request.user.role == 'staff':
            return redirect('inventory:attendance_dashboard')
        else:
            return redirect('inventory:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            log_user_action(
                user=user,
                action_type='login',
                target_model='User',
                description=f"User logged in",
                request=request
            )
            
            # Redirect based on user role
            if user.is_supplier_user():
                messages.success(request, f"Welcome back, {user.supplier.name}!")
                return redirect('inventory:supplier_dashboard')
            elif user.role == 'staff':
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                return redirect('inventory:attendance_dashboard')
            else:
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                return redirect('inventory:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'inventory/login.html')


@login_required
def dashboard(request):
    """
    Main dashboard view
    """
    # Supplier users: redirect to supplier dashboard
    if request.user.is_supplier_user():
        return redirect('inventory:supplier_dashboard')
    
    # Staff users: redirect to attendance dashboard
    if request.user.role == 'staff':
        return redirect('inventory:attendance_dashboard')

    from django.db.models import Sum, F, DecimalField, ExpressionWrapper
    from datetime import timedelta
    
    # Calculate total products (active items)
    total_products = Item.objects.filter(is_active=True).count()
    
    # Calculate total inventory value (sum of stock lots)
    total_value = StockLot.objects.filter(
        qty__gt=0
    ).aggregate(
        total=Sum(ExpressionWrapper(
            F('qty') * F('unit_cost'),
            output_field=DecimalField()
        ))
    )['total'] or 0
    
    # Calculate low stock items (items below reorder level)
    low_stock_count = 0
    out_of_stock_count = 0
    finished_goods_count = 0
    finished_goods_low_stock = 0
    finished_goods_value = 0
    
    for item in Item.objects.filter(is_active=True):
        current_stock = item.get_current_stock()
        
        # Count finished goods
        if item.category == 'finished_good':
            finished_goods_count += 1
            # Calculate finished goods value
            fg_value = StockLot.objects.filter(
                item=item,
                qty__gt=0
            ).aggregate(
                total=Sum(ExpressionWrapper(
                    F('qty') * F('unit_cost'),
                    output_field=DecimalField()
                ))
            )['total'] or 0
            finished_goods_value += float(fg_value)
            
            # Check if finished good is low stock
            if current_stock <= item.reorder_level and current_stock > 0:
                finished_goods_low_stock += 1
        
        # Count all low stock
        if current_stock == 0:
            out_of_stock_count += 1
        elif current_stock <= item.reorder_level:
            low_stock_count += 1
    
    # Get recent items with stock information (last 5 items updated)
    recent_items = Item.objects.filter(is_active=True).order_by('-updated_at')[:5]
    recent_items_data = []
    for item in recent_items:
        current_stock = item.get_current_stock()
        item_value = StockLot.objects.filter(
            item=item,
            qty__gt=0
        ).aggregate(
            total=Sum(ExpressionWrapper(
                F('qty') * F('unit_cost'),
                output_field=DecimalField()
            ))
        )['total'] or 0
        
        # Determine status
        if current_stock == 0:
            status = 'Out of Stock'
            status_class = 'danger'
        elif current_stock <= item.reorder_level:
            status = 'Low Stock'
            status_class = 'warning'
        else:
            status = 'In Stock'
            status_class = 'success'
        
        recent_items_data.append({
            'item': item,
            'current_stock': current_stock,
            'value': item_value,
            'status': status,
            'status_class': status_class,
        })
    
    # Get monthly data for stock value trend (last 6 months)
    monthly_values = []
    monthly_labels = []
    current_date = timezone.now()
    
    for i in range(6):
        # Calculate month offset
        month_date = current_date - timedelta(days=30 * (5 - i))
        month_label = month_date.strftime('%b')
        monthly_labels.append(month_label)
        
        # Get total stock value at that time
        month_value = StockLot.objects.filter(
            received_at__lte=month_date,
            qty__gt=0
        ).aggregate(
            total=Sum(ExpressionWrapper(
                F('qty') * F('unit_cost'),
                output_field=DecimalField()
            ))
        )['total'] or 0
        
        monthly_values.append(float(month_value))
    
    # Calculate previous month statistics for comparison
    prev_month_date = current_date - timedelta(days=30)
    
    prev_total_value = StockLot.objects.filter(
        received_at__lte=prev_month_date,
        qty__gt=0
    ).aggregate(
        total=Sum(ExpressionWrapper(
            F('qty') * F('unit_cost'),
            output_field=DecimalField()
        ))
    )['total'] or 0
    
    # Calculate percentage changes
    value_change = 0
    if prev_total_value > 0:
        value_change = ((float(total_value) - float(prev_total_value)) / float(prev_total_value)) * 100
    
    context = {
        'user': request.user,
        'permissions': get_user_permissions(request.user),
        'recent_activities': AuditLog.objects.select_related('user').order_by('-timestamp')[:6],
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'finished_goods_count': finished_goods_count,
        'finished_goods_low_stock': finished_goods_low_stock,
        'finished_goods_value': finished_goods_value,
        'recent_items_data': recent_items_data,
        'monthly_values': json.dumps(monthly_values),
        'monthly_labels': json.dumps(monthly_labels),
        'value_change': value_change,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def attendance_dashboard(request):
    """Staff self-attendance view with today's record and calendar view."""
    from calendar import monthcalendar, month_name
    from datetime import datetime, timedelta
    
    if request.user.role not in ['staff', 'admin', 'super_admin']:
        messages.error(request, "Unauthorized")
        return redirect('inventory:dashboard')

    today = timezone.now().date()
    
    # Get month/year from query params or use current
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month
    
    # Staff can only see their own; admin/super_admin can switch user via param later
    target_user = request.user
    
    # Get all records for the selected month
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    records = AttendanceRecord.objects.filter(
        user=target_user,
        date__gte=month_start,
        date__lte=month_end
    )
    
    # Create a dictionary for quick lookup
    records_dict = {rec.date: rec for rec in records}
    
    # Get today's record
    try:
        record_today = AttendanceRecord.objects.get(user=target_user, date=today)
    except AttendanceRecord.DoesNotExist:
        record_today = None
    
    # Generate calendar
    cal = monthcalendar(year, month)
    
    # Build calendar data with attendance info
    calendar_weeks = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0})
            else:
                date = datetime(year, month, day).date()
                record = records_dict.get(date)
                week_data.append({
                    'day': day,
                    'date': date,
                    'is_today': date == today,
                    'record': record,
                    'has_record': record is not None,
                    'is_complete': record.is_am_complete() and record.is_pm_complete() if record else False,
                    'is_partial': (record.is_am_complete() or record.is_pm_complete()) and not (record.is_am_complete() and record.is_pm_complete()) if record else False,
                })
        calendar_weeks.append(week_data)
    
    # Calculate prev/next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    # Get today's production for staff dashboard
    manila_tz = pytz.timezone('Asia/Manila')
    manila_now = timezone.now().astimezone(manila_tz)
    today_date = manila_now.date()
    
    # Get start and end of today in Manila time
    today_start = manila_tz.localize(datetime.combine(today_date, datetime.min.time()))
    today_end = manila_tz.localize(datetime.combine(today_date, datetime.max.time()))
    
    today_productions = StockMovement.objects.filter(
        movement_type='produce',
        timestamp__gte=today_start,
        timestamp__lte=today_end
    ).select_related('item', 'lot', 'created_by').order_by('-timestamp')
    
    today_total_items = today_productions.count()
    today_total_qty = sum(p.qty for p in today_productions)
    
    # Calculate ingredients for today's productions in staff dashboard
    for production in today_productions:
        try:
            recipe = Recipe.objects.filter(product=production.item, is_active=True).first()
            if recipe:
                ingredients_used = []
                for recipe_item in recipe.recipe_items.all():
                    qty_needed = float(recipe_item.qty) * float(production.qty) / float(recipe.yield_qty)
                    qty_needed = qty_needed * recipe_item.get_adjusted_qty() / float(recipe_item.qty)
                    ingredients_used.append({
                        'ingredient': recipe_item.ingredient,
                        'qty': qty_needed,
                        'unit': recipe_item.unit
                    })
                production.ingredients_used = ingredients_used
            else:
                production.ingredients_used = []
        except Exception:
            production.ingredients_used = []

    context = {
        'target_user': target_user,
        'record_today': record_today,
        'now': get_manila_now(),
        'calendar_weeks': calendar_weeks,
        'current_month': month_name[month],
        'current_year': year,
        'current_month_num': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'records_dict': records_dict,
        'today_productions': today_productions,
        'today_total_items': today_total_items,
        'today_total_qty': today_total_qty,
        'today': today,
    }
    return render(request, 'inventory/attendance_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def clock_event(request):
    """Clock in/out with AM/PM constraints; staff can only clock self."""
    if request.user.role not in ['staff', 'admin', 'super_admin']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    action = request.POST.get('action')  # time_in_am, time_out_am, time_in_pm, time_out_pm
    # Use Manila-aware current time to determine "today" and record timestamps
    now_dt = get_manila_now()
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
    
    # Super admin can view anyone
    # Admin can view all users (admin, supplier, staff) except super_admin
    # Staff can only view themselves
    if request.user.role == 'super_admin':
        # Super admin can view and manage anyone
        can_view = True
        can_edit = True
    elif request.user.role == 'admin':
        # Admin can view all users except super_admin
        if user.role == 'super_admin':
            messages.error(request, "You don't have permission to view Super Admin users.")
            return redirect('inventory:user_list')
        can_view = True
        # Admin can only edit staff users, not other admins or suppliers
        can_edit = (user.role == 'staff')
    else:
        # Staff can only view themselves
        if request.user != user:
            messages.error(request, "You don't have permission to view this user.")
            return redirect('inventory:user_list')
        can_view = True
        can_edit = False
    
    user_accesses = UserAccess.objects.filter(user=user, is_active=True)
    user_links = UserLinks.objects.filter(user=user, is_active=True)
    
    # Show info message if admin is viewing another admin or supplier (read-only)
    if request.user.role == 'admin' and user.role in ['admin', 'supplier'] and request.user != user:
        messages.info(request, f"You are viewing this {user.get_role_display()} user in read-only mode. You can only edit Staff users.")
    
    context = {
        'target_user': user,
        'user_accesses': user_accesses,
        'user_links': user_links,
        'can_manage': can_edit,  # Use can_edit instead of can_manage_user for more granular control
        'is_read_only': not can_edit,
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
            return redirect('inventory:user_list')
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
    # Super admin can edit anyone
    # Admin can only edit staff users
    if request.user.role == 'super_admin':
        # Super admin can edit anyone
        pass
    elif request.user.role == 'admin':
        # Admin can only edit staff users, not other admins or suppliers
        if user.role in ['admin', 'supplier', 'super_admin']:
            messages.error(request, f"You don't have permission to edit {user.get_role_display()} users. You can only edit Staff users.")
            return redirect('inventory:user_detail', user_id=user_id)
    else:
        # Staff cannot edit anyone
        messages.error(request, "You don't have permission to edit users.")
        return redirect('inventory:user_list')
    
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
            return redirect('inventory:user_detail', user_id=user.id)
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
        return redirect('inventory:user_list')
    
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
        return redirect('inventory:user_list')
    
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
        return redirect('inventory:dashboard')
    
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
    today_records = AttendanceRecord.objects.filter(date=get_manila_now().date()).count()
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


# --- DEBUG VIEWS ---

@login_required
def nav_debug(request):
    """
    Debug view to test navigation
    """
    return render(request, 'inventory/nav_debug.html')

# --- INVENTORY MANAGEMENT VIEWS ---

@login_required
@permission_required('inventory_read')
def inventory_dashboard(request):
    """
    Bakery inventory dashboard with KPIs, analytics, and line graphs
    """
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta, datetime
    import json
    
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
    
    # Bakery-specific analytics
    bakery_analytics = {
        'total_ingredients': Item.objects.filter(category='ingredient', is_active=True).count(),
        'total_finished_goods': Item.objects.filter(category='finished_good', is_active=True).count(),
        'total_recipes': Recipe.objects.filter(is_active=True).count(),
        'active_suppliers': Supplier.objects.filter(is_active=True).count(),
    }
    
    # Production analytics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    production_stats = {
        'total_productions': StockMovement.objects.filter(
            movement_type='produce',
            timestamp__gte=thirty_days_ago
        ).count(),
        'total_consumption': StockMovement.objects.filter(
            movement_type='consume',
            timestamp__gte=thirty_days_ago
        ).count(),
        'total_receipts': StockMovement.objects.filter(
            movement_type='receive',
            timestamp__gte=thirty_days_ago
        ).count(),
    }
    
    # Daily production trend (last 7 days)
    daily_production = []
    daily_consumption = []
    daily_receipts = []
    date_labels = []
    
    for i in range(7):
        date = timezone.now().date() - timedelta(days=6-i)
        date_labels.append(date.strftime('%m/%d'))
        
        # Production
        prod_count = StockMovement.objects.filter(
            movement_type='produce',
            timestamp__date=date
        ).count()
        daily_production.append(prod_count)
        
        # Consumption
        cons_count = StockMovement.objects.filter(
            movement_type='consume',
            timestamp__date=date
        ).count()
        daily_consumption.append(cons_count)
        
        # Receipts
        rec_count = StockMovement.objects.filter(
            movement_type='receive',
            timestamp__date=date
        ).count()
        daily_receipts.append(rec_count)
    
    # Top selling items (by consumption)
    top_consumed_items = StockMovement.objects.filter(
        movement_type='consume',
        timestamp__gte=thirty_days_ago
    ).values('item__name', 'item__code').annotate(
        total_qty=Sum('qty')
    ).order_by('-total_qty')[:5]
    
    # Category distribution
    category_distribution = Item.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Expiry trend (next 30 days)
    expiry_trend = []
    expiry_labels = []
    for i in range(30):
        date = timezone.now().date() + timedelta(days=i)
        expiry_labels.append(date.strftime('%m/%d'))
        
        expiring_count = StockLot.objects.filter(
            qty__gt=0,
            expires_at=date,
            expires_at__isnull=False
        ).count()
        expiry_trend.append(expiring_count)
    
    context = {
        'stock_summary': stock_summary,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'expired_items': expired_items,
        'recent_movements': recent_movements,
        'bakery_analytics': bakery_analytics,
        'production_stats': production_stats,
        'daily_production': json.dumps(daily_production),
        'daily_consumption': json.dumps(daily_consumption),
        'daily_receipts': json.dumps(daily_receipts),
        'date_labels': json.dumps(date_labels),
        'top_consumed_items': top_consumed_items,
        'category_distribution': category_distribution,
        'expiry_trend': json.dumps(expiry_trend),
        'expiry_labels': json.dumps(expiry_labels),
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
                lot_no = form.cleaned_data.get('lot_no')
                # Auto-generate lot number if not provided
                if not lot_no:
                    import datetime
                    item = form.cleaned_data['item']
                    now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    lot_no = f"LOT-{item.code}-{now_str}"

                lot = InventoryService.receive_stock(
                    item=form.cleaned_data['item'],
                    lot_no=lot_no,
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
def api_item_lots(request):
    """Return available lots for an item ordered by FEFO/FIFO as JSON."""
    item_id = request.GET.get('item_id')
    if not item_id:
        return HttpResponseBadRequest('item_id required')

    try:
        from .models import Item
        item = Item.objects.get(id=item_id)
    except Exception:
        return HttpResponseBadRequest('invalid item_id')

    lots = InventoryService.get_available_lots(item)
    data = []
    for lot in lots:
        data.append({
            'id': str(lot.id),
            'lot_no': lot.lot_no,
            'qty': str(lot.qty),
            'unit': lot.unit,
            'expires_at': lot.expires_at.isoformat() if lot.expires_at else None,
        })

    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)


@login_required
def api_item_meta(request):
    """Return metadata for an item (is_perishable, unit, shelf_life_days) as JSON."""
    item_id = request.GET.get('item_id')
    if not item_id:
        return HttpResponseBadRequest('item_id required')

    try:
        from .models import Item
        item = Item.objects.get(id=item_id)
    except Exception:
        return HttpResponseBadRequest('invalid item_id')

    data = {
        'is_perishable': item.is_perishable,
        'unit': item.unit,
        'shelf_life_days': item.shelf_life_days,
        'code': item.code,
        'name': item.name,
        'current_stock': item.get_current_stock(),
    }

    return JsonResponse(data, encoder=DjangoJSONEncoder)


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
                unit_cost = form.cleaned_data.get('unit_cost')
                
                # Auto-calculate unit cost if not provided
                if not unit_cost:
                    total_cost = RecipeService.calculate_recipe_cost(recipe)
                    unit_cost = total_cost / recipe.yield_qty if recipe.yield_qty > 0 else 0
                    messages.info(request, f"Unit cost auto-calculated: ₱{unit_cost:.2f} per {recipe.get_yield_unit_display()}")
                
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
                    notes=form.cleaned_data.get('notes'),
                    unit_cost=unit_cost
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
def production_list(request):
    """
    List all production records with filtering
    """
    from datetime import datetime, timedelta
    
    # Get filter parameters
    date_filter = request.GET.get('date', '')
    recipe_filter = request.GET.get('recipe', '')
    
    # Get production records (StockMovements with type='produce')
    productions = StockMovement.objects.filter(
        movement_type='produce'
    ).select_related('item', 'lot', 'created_by').order_by('-timestamp')
    
    # Apply date filter
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            productions = productions.filter(timestamp__date=filter_date)
        except ValueError:
            pass
    
    # Apply recipe filter
    if recipe_filter:
        productions = productions.filter(item__name__icontains=recipe_filter)
    
    # Get today's production for quick view
    # Use Manila timezone
    manila_tz = pytz.timezone('Asia/Manila')
    manila_now = timezone.now().astimezone(manila_tz)
    today = manila_now.date()
    
    # Get start and end of today in Manila time
    today_start = manila_tz.localize(datetime.combine(today, datetime.min.time()))
    today_end = manila_tz.localize(datetime.combine(today, datetime.max.time()))
    
    today_productions = StockMovement.objects.filter(
        movement_type='produce',
        timestamp__gte=today_start,
        timestamp__lte=today_end
    ).select_related('item', 'lot', 'created_by').order_by('-timestamp')
    
    # Calculate today's summary
    today_total_items = today_productions.count()
    today_total_qty = sum(p.qty for p in today_productions)
    
    # Pagination
    paginator = Paginator(productions, 20)
    page_number = request.GET.get('page')
    productions = paginator.get_page(page_number)
    
    # Calculate ingredients used for each production
    for production in productions:
        # Calculate total value
        if production.lot and production.lot.unit_cost:
            production.total_value = float(production.qty) * float(production.lot.unit_cost)
        else:
            production.total_value = None
            
        # Find the recipe for this product (get the first active one if multiple exist)
        try:
            recipe = Recipe.objects.filter(product=production.item, is_active=True).first()
            if recipe:
                # Calculate ingredients needed based on production quantity
                ingredients_used = []
                for recipe_item in recipe.recipe_items.all():
                    qty_needed = float(recipe_item.qty) * float(production.qty) / float(recipe.yield_qty)
                    # Apply loss factor if any
                    qty_needed = qty_needed * recipe_item.get_adjusted_qty() / float(recipe_item.qty)
                    ingredients_used.append({
                        'ingredient': recipe_item.ingredient,
                        'qty': qty_needed,
                        'unit': recipe_item.unit
                    })
                production.ingredients_used = ingredients_used
            else:
                production.ingredients_used = []
        except Exception:
            production.ingredients_used = []
    
    # Calculate ingredients for today's productions
    for production in today_productions:
        try:
            recipe = Recipe.objects.filter(product=production.item, is_active=True).first()
            if recipe:
                ingredients_used = []
                for recipe_item in recipe.recipe_items.all():
                    qty_needed = float(recipe_item.qty) * float(production.qty) / float(recipe.yield_qty)
                    qty_needed = qty_needed * recipe_item.get_adjusted_qty() / float(recipe_item.qty)
                    ingredients_used.append({
                        'ingredient': recipe_item.ingredient,
                        'qty': qty_needed,
                        'unit': recipe_item.unit
                    })
                production.ingredients_used = ingredients_used
            else:
                production.ingredients_used = []
        except Exception:
            production.ingredients_used = []
    
    # Get all recipes for filter dropdown
    recipes = Recipe.objects.filter(is_active=True).values_list('product__name', flat=True).distinct()
    
    context = {
        'productions': productions,
        'today_productions': today_productions,
        'today_total_items': today_total_items,
        'today_total_qty': today_total_qty,
        'date_filter': date_filter,
        'recipe_filter': recipe_filter,
        'recipes': recipes,
        'today': today,
    }
    
    return render(request, 'inventory/production_list.html', context)


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
    Create new supplier with optional user account
    """
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            
            # Create user account if requested
            if form.cleaned_data.get('create_user_account'):
                # Generate username from first and last name
                first_name = form.cleaned_data['user_first_name']
                last_name = form.cleaned_data['user_last_name']
                base_username = f"{first_name.lower()}.{last_name.lower()}"
                username = base_username
                
                # Check if username exists and add number if needed
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create the user account
                user = User.objects.create_user(
                    username=username,
                    email=supplier.email,
                    password=form.cleaned_data['user_password'],
                    first_name=first_name,
                    last_name=last_name,
                    role='supplier',
                    phone_number=supplier.phone,
                    address=supplier.address,
                    is_active=True
                )
                user.created_by = request.user
                user.supplier = supplier
                user.save()
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='User',
                    target_id=user.id,
                    description=f"Created supplier user account {user.username} for supplier {supplier.name}",
                    request=request
                )
                
                messages.success(request, f"Supplier {supplier.name} created successfully with user account '{username}'. They can now login to the supplier portal.")
            else:
                messages.success(request, f"Supplier {supplier.name} created successfully.")
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='Supplier',
                target_id=supplier.id,
                description=f"Created supplier {supplier.name}",
                request=request
            )
            
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
    Create new recipe with ingredients and steps
    """
    if request.method == 'POST':
        # Debug: Print all POST data
        print("=" * 50)
        print("POST DATA RECEIVED:")
        for key, value in request.POST.items():
            print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")
        print("=" * 50)
        
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()
            
            # Process ingredients data from JSON
            ingredients_data = request.POST.get('ingredients_data', '')
            ingredients_added = 0
            
            print(f"Ingredients data received: '{ingredients_data}'")
            
            if ingredients_data:
                try:
                    import json
                    ingredients = json.loads(ingredients_data)
                    for ing_data in ingredients:
                        ingredient_id = ing_data.get('ingredient_id')
                        qty = ing_data.get('qty')
                        unit = ing_data.get('unit')
                        
                        if ingredient_id and qty:
                            RecipeItem.objects.create(
                                recipe=recipe,
                                ingredient_id=ingredient_id,
                                qty=qty,
                                unit=unit,
                                loss_factor=0
                            )
                            ingredients_added += 1
                except (json.JSONDecodeError, Exception) as e:
                    messages.warning(request, f"Error adding ingredients: {str(e)}")
            else:
                messages.warning(request, "No ingredients data received. Please make sure to add at least one ingredient.")
            
            if ingredients_added > 0:
                messages.info(request, f"Added {ingredients_added} ingredient(s) to the recipe.")
            
            log_user_action(
                user=request.user,
                action_type='create',
                target_model='Recipe',
                target_id=recipe.id,
                description=f"Created recipe {recipe.name}",
                request=request
            )
            
            messages.success(request, f"Recipe '{recipe.name}' created successfully!")
            return redirect('inventory:recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm()
    
    # Get all active ingredients for the ingredient selector
    ingredients = Item.objects.filter(category='ingredient', is_active=True).order_by('name')
    
    context = {
        'form': form,
        'title': 'Create Recipe',
        'ingredients': ingredients,
    }
    
    return render(request, 'inventory/recipe_form.html', context)


@login_required
@permission_required('reports_read')
def stock_report(request):
    """
    Comprehensive stock report with date range, consumption tracking, and analytics
    Supports CSV export
    """
    import csv
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q
    from django.http import HttpResponse
    from decimal import Decimal
    
    # Get filters
    category_filter = request.GET.get('category', '')
    low_stock_only = request.GET.get('low_stock', False)
    report_type = request.GET.get('report_type', 'current')  # current, monthly, yearly
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range based on report type
    today = timezone.now().date()
    if report_type == 'monthly' and not date_from:
        date_from = (today.replace(day=1)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    elif report_type == 'yearly' and not date_from:
        date_from = (today.replace(month=1, day=1)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    
    # Parse dates
    start_date = None
    end_date = None
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    items = Item.objects.filter(is_active=True)
    
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Build report data
    report_data = []
    total_value = Decimal('0.00')
    total_consumed = Decimal('0.00')
    total_received = Decimal('0.00')
    total_produced = Decimal('0.00')
    
    for item in items:
        current_stock = item.get_current_stock()
        is_low_stock = item.is_low_stock()
        
        if low_stock_only and not is_low_stock:
            continue
        
        # Calculate consumption, receipts, and production for date range
        movements = StockMovement.objects.filter(item=item)
        if start_date:
            movements = movements.filter(timestamp__date__gte=start_date)
        if end_date:
            movements = movements.filter(timestamp__date__lte=end_date)
        
        # Consumption
        consumed = movements.filter(movement_type='consume').aggregate(
            total=Sum('qty')
        )['total'] or Decimal('0.00')
        
        # Receipts
        received = movements.filter(movement_type='receive').aggregate(
            total=Sum('qty')
        )['total'] or Decimal('0.00')
        
        # Production
        produced = movements.filter(movement_type='produce').aggregate(
            total=Sum('qty')
        )['total'] or Decimal('0.00')
        
        # Adjustments
        adjusted = movements.filter(movement_type='adjust').aggregate(
            total=Sum('qty')
        )['total'] or Decimal('0.00')
        
        # Calculate value
        unit_cost = InventoryService.calculate_item_cost(item)
        item_value = current_stock * unit_cost
        total_value += item_value
        
        # Track totals
        total_consumed += consumed
        total_received += received
        total_produced += produced
        
        report_data.append({
            'item': item,
            'current_stock': current_stock,
            'reorder_level': item.reorder_level,
            'is_low_stock': is_low_stock,
            'expiring_soon': item.get_expiring_soon().count(),
            'unit_cost': unit_cost,
            'item_value': item_value,
            'consumed': consumed,
            'received': received,
            'produced': produced,
            'adjusted': adjusted,
        })
    
    # Summary statistics
    summary = {
        'total_items': len(report_data),
        'low_stock_count': sum(1 for d in report_data if d['is_low_stock']),
        'expiring_count': sum(1 for d in report_data if d['expiring_soon'] > 0),
        'total_value': total_value,
        'total_consumed': total_consumed,
        'total_received': total_received,
        'total_produced': total_produced,
    }
    
    # Check if CSV export is requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="stock_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Item Code',
            'Item Name',
            'Category',
            'Current Stock',
            'Unit',
            'Reorder Level',
            'Status',
            'Unit Cost',
            'Total Value',
            'Consumed',
            'Received',
            'Produced',
            'Adjusted',
            'Expiring Soon'
        ])
        
        # Write data rows
        for data in report_data:
            status = 'Low Stock' if data['is_low_stock'] else 'OK'
            writer.writerow([
                data['item'].code,
                data['item'].name,
                data['item'].get_category_display(),
                f"{data['current_stock']:.2f}",
                data['item'].get_unit_display(),
                f"{data['reorder_level']:.2f}",
                status,
                f"{data['unit_cost']:.2f}",
                f"{data['item_value']:.2f}",
                f"{data['consumed']:.2f}",
                f"{data['received']:.2f}",
                f"{data['produced']:.2f}",
                f"{data['adjusted']:.2f}",
                data['expiring_soon']
            ])
        
        # Write summary row
        writer.writerow([])
        writer.writerow(['SUMMARY'])
        writer.writerow(['Total Items', summary['total_items']])
        writer.writerow(['Low Stock Items', summary['low_stock_count']])
        writer.writerow(['Items with Expiring Stock', summary['expiring_count']])
        writer.writerow(['Total Inventory Value', f"₱{summary['total_value']:.2f}"])
        writer.writerow(['Total Consumed', f"{summary['total_consumed']:.2f}"])
        writer.writerow(['Total Received', f"{summary['total_received']:.2f}"])
        writer.writerow(['Total Produced', f"{summary['total_produced']:.2f}"])
        
        if date_from or date_to:
            writer.writerow([])
            writer.writerow(['Report Period'])
            writer.writerow(['From', date_from or 'Beginning'])
            writer.writerow(['To', date_to or 'Today'])
        
        return response
    
    context = {
        'report_data': report_data,
        'summary': summary,
        'category_filter': category_filter,
        'low_stock_only': low_stock_only,
        'report_type': report_type,
        'date_from': date_from,
        'date_to': date_to,
        'category_choices': Item.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/stock_report.html', context)


# --- PURCHASE ORDER VIEWS ---

@login_required
@permission_required('inventory_write')
def purchase_order_list(request):
    """
    List all purchase orders with filtering
    """
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    
    orders = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if supplier_filter:
        orders = orders.filter(supplier__id=supplier_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Get summary statistics
    order_summary = PurchaseOrderService.get_order_summary()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'supplier_filter': supplier_filter,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'suppliers': Supplier.objects.filter(is_active=True),
        'order_summary': order_summary,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='PurchaseOrder',
        description="Viewed purchase order list",
        request=request
    )
    
    return render(request, 'inventory/purchase_order_list.html', context)


@login_required
@permission_required('inventory_read')
def purchase_order_detail(request, order_id):
    """
    View purchase order details with QR code
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)
    
    # Generate QR code image
    qr_code_image = PurchaseOrderService.generate_qr_code_image(order.qr_code)
    
    # Get order items
    order_items = order.order_items.select_related('item').all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'qr_code_image': qr_code_image,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='PurchaseOrder',
        target_id=order_id,
        description=f"Viewed purchase order {order.order_no}",
        request=request
    )
    
    return render(request, 'inventory/purchase_order_detail.html', context)


@login_required
@permission_required('inventory_write')
def purchase_order_receive(request, order_id):
    """
    Display receiving form with expiration date inputs, then process the receiving
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)
    
    # Check if order can be received
    if order.status not in ['approved', 'shipped']:
        messages.error(request, "This order cannot be received in its current status.")
        return redirect('inventory:purchase_order_detail', order_id=order.id)
    
    if request.method == 'POST':
        # Process the receiving
        try:
            order_items = order.order_items.all()
            
            for item in order_items:
                qty_received = request.POST.get(f'qty_received_{item.id}')
                lot_no = request.POST.get(f'lot_no_{item.id}')
                expires_at = request.POST.get(f'expires_at_{item.id}')
                notes = request.POST.get(f'notes_{item.id}', '')
                
                if qty_received and float(qty_received) > 0:
                    # Create stock lot
                    stock_lot = StockLot.objects.create(
                        item=item.item,
                        lot_no=lot_no,
                        qty=qty_received,
                        unit=item.unit,
                        expires_at=expires_at if expires_at else None,
                        unit_cost=item.unit_price,
                        supplier=order.supplier,
                        notes=notes,
                        created_by=request.user
                    )
                    
                    # Create stock movement
                    StockMovement.objects.create(
                        item=item.item,
                        lot=stock_lot,
                        movement_type='receive',
                        qty=qty_received,
                        unit=item.unit,
                        ref_no=order.order_no,
                        reason=f"Received from PO {order.order_no}",
                        notes=notes,
                        created_by=request.user
                    )
                    
                    # Update order item qty_received
                    item.qty_received = float(qty_received)
                    item.save()
            
            # Update order status
            order.status = 'received'
            order.received_by = request.user
            order.received_at = timezone.now()
            order.actual_delivery_date = timezone.now().date()
            
            # Add delivery notes if provided
            delivery_notes = request.POST.get('delivery_notes', '')
            if delivery_notes:
                order.notes = (order.notes or '') + f"\n\nDelivery Notes: {delivery_notes}"
            
            order.save()
            
            # Log action
            log_user_action(
                user=request.user,
                action_type='update',
                target_model='PurchaseOrder',
                target_id=order.id,
                description=f"Received purchase order {order.order_no}",
                request=request
            )
            
            messages.success(request, f"Purchase order {order.order_no} has been successfully received!")
            return redirect('inventory:purchase_order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"Error receiving order: {str(e)}")
            return redirect('inventory:purchase_order_receive', order_id=order.id)
    
    # GET request - show the form
    order_items = order.order_items.select_related('item').all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'today': timezone.now().date(),
    }
    
    return render(request, 'inventory/purchase_order_receive.html', context)


@login_required
@permission_required('inventory_write')
def purchase_order_create(request):
    """
    Create new purchase order with items (no prices yet - supplier fills prices during approval)
    """
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        
        # Get items data from POST (quantities only, no prices)
        items_data = []
        item_count = int(request.POST.get('item_count', 0))
        
        for i in range(item_count):
            item_id = request.POST.get(f'item_{i}')
            qty = request.POST.get(f'qty_{i}')
            notes = request.POST.get(f'item_notes_{i}', '')
            
            if item_id and qty:
                try:
                    item = Item.objects.get(id=item_id)
                    items_data.append({
                        'item': item,
                        'qty': Decimal(qty),
                        'unit_price': Decimal('0'),  # Price will be set by supplier
                        'notes': notes
                    })
                except (Item.DoesNotExist, ValueError):
                    pass
        
        if form.is_valid() and items_data:
            try:
                po = PurchaseOrderService.create_purchase_order(
                    supplier=form.cleaned_data['supplier'],
                    items_data=items_data,
                    user=request.user,
                    notes=form.cleaned_data.get('notes'),
                    expected_delivery_date=None  # Will be set by supplier
                )
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='PurchaseOrder',
                    target_id=po.id,
                    description=f"Created purchase order {po.order_no}",
                    request=request
                )
                
                messages.success(request, f"Purchase order {po.order_no} created successfully. Waiting for supplier approval and pricing.")
                return redirect('inventory:purchase_order_detail', order_id=po.id)
            except Exception as e:
                messages.error(request, f"Error creating purchase order: {str(e)}")
        else:
            if not items_data:
                messages.error(request, "Please add at least one item to the purchase order.")
    else:
        form = PurchaseOrderForm()
    
    # Get all active items for selection
    items = Item.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'items': items,
        'title': 'Create Purchase Order',
    }
    
    return render(request, 'inventory/purchase_order_form.html', context)


@login_required
@permission_required('inventory_write')
def purchase_order_approve(request, order_id):
    """
    Approve purchase order with pricing (staff simulating supplier action)
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)
    
    if not order.can_be_approved():
        messages.error(request, f"Purchase order cannot be approved. Current status: {order.get_status_display()}")
        return redirect('inventory:purchase_order_detail', order_id=order_id)
    
    order_items = order.order_items.all()
    
    if request.method == 'POST':
        form = PurchaseOrderApproveForm(request.POST, order_items=order_items)
        if form.is_valid():
            try:
                # Update item prices from form
                item_prices = form.get_item_prices()
                for po_item in order_items:
                    price_key = str(po_item.id)
                    if price_key in item_prices:
                        po_item.unit_price = item_prices[price_key]
                        po_item.save()
                
                # Recalculate total
                order.total_amount = order.calculate_total()
                order.save()
                
                # Approve order
                PurchaseOrderService.approve_purchase_order(
                    po=order,
                    supplier_notes=form.cleaned_data.get('supplier_notes'),
                    expected_delivery_date=form.cleaned_data['expected_delivery_date']
                )
                
                log_user_action(
                    user=request.user,
                    action_type='update',
                    target_model='PurchaseOrder',
                    target_id=order_id,
                    description=f"Approved purchase order {order.order_no} with pricing",
                    request=request
                )
                
                messages.success(request, f"Purchase order {order.order_no} approved successfully with pricing.")
                return redirect('inventory:purchase_order_detail', order_id=order_id)
            except Exception as e:
                messages.error(request, f"Error approving purchase order: {str(e)}")
    else:
        form = PurchaseOrderApproveForm(
            initial={'expected_delivery_date': order.expected_delivery_date},
            order_items=order_items
        )
    
    context = {
        'form': form,
        'order': order,
        'order_items': order_items,
        'title': f'Approve Purchase Order: {order.order_no}',
    }
    
    return render(request, 'inventory/purchase_order_approve.html', context)


@login_required
@permission_required('inventory_write')
def purchase_order_ship(request, order_id):
    """
    Mark purchase order as shipped
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)
    
    if not order.can_be_shipped():
        messages.error(request, f"Purchase order cannot be shipped. Current status: {order.get_status_display()}")
        return redirect('inventory:purchase_order_detail', order_id=order_id)
    
    if request.method == 'POST':
        try:
            PurchaseOrderService.ship_purchase_order(order)
            
            log_user_action(
                user=request.user,
                action_type='update',
                target_model='PurchaseOrder',
                target_id=order_id,
                description=f"Marked purchase order {order.order_no} as shipped",
                request=request
            )
            
            messages.success(request, f"Purchase order {order.order_no} marked as shipped.")
        except Exception as e:
            messages.error(request, f"Error shipping purchase order: {str(e)}")
    
    return redirect('inventory:purchase_order_detail', order_id=order_id)


@login_required
@permission_required('inventory_write')
def purchase_order_scan_receive(request):
    """
    Scan QR code to receive purchase order
    """
    if request.method == 'POST':
        form = QRCodeScanForm(request.POST)
        if form.is_valid():
            qr_code = form.cleaned_data['qr_code']
            
            try:
                po, received_lots = PurchaseOrderService.receive_purchase_order_by_qr(
                    qr_code=qr_code,
                    user=request.user
                )
                
                log_user_action(
                    user=request.user,
                    action_type='update',
                    target_model='PurchaseOrder',
                    target_id=po.id,
                    description=f"Received purchase order {po.order_no} via QR scan",
                    request=request
                )
                
                messages.success(request, f"Purchase order {po.order_no} received successfully! {len(received_lots)} items added to inventory.")
                return redirect('inventory:purchase_order_detail', order_id=po.id)
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error receiving purchase order: {str(e)}")
    else:
        form = QRCodeScanForm()
    
    # Get orders waiting to be received
    shipped_orders = PurchaseOrderService.get_shipped_orders()
    
    context = {
        'form': form,
        'shipped_orders': shipped_orders,
        'title': 'Receive Purchase Order',
    }
    
    return render(request, 'inventory/purchase_order_scan.html', context)


@login_required
@permission_required('inventory_write')
def purchase_order_cancel(request, order_id):
    """
    Cancel purchase order
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)
    
    if order.status == 'received':
        messages.error(request, "Cannot cancel a received purchase order.")
        return redirect('inventory:purchase_order_detail', order_id=order_id)
    
    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        
        log_user_action(
            user=request.user,
            action_type='update',
            target_model='PurchaseOrder',
            target_id=order_id,
            description=f"Cancelled purchase order {order.order_no}",
            request=request
        )
        
        messages.success(request, f"Purchase order {order.order_no} cancelled.")
        return redirect('inventory:purchase_order_list')
    
    return redirect('inventory:purchase_order_detail', order_id=order_id)


# --- SUPPLIER PORTAL VIEWS ---

@login_required
@supplier_required
def supplier_dashboard(request):
    """
    Supplier portal dashboard
    """
    supplier = request.user.supplier
    
    # Get order statistics
    orders = PurchaseOrder.objects.filter(supplier=supplier)
    pending_orders = orders.filter(status='pending').count()
    approved_orders = orders.filter(status='approved').count()
    shipped_orders = orders.filter(status='shipped').count()
    received_orders = orders.filter(status='received').count()
    
    # Get recent orders
    recent_orders = orders.order_by('-created_at')[:5]
    
    # Calculate total order value
    from django.db.models import Sum
    total_order_value = orders.filter(status__in=['approved', 'shipped', 'received']).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'supplier': supplier,
        'pending_orders': pending_orders,
        'approved_orders': approved_orders,
        'shipped_orders': shipped_orders,
        'received_orders': received_orders,
        'recent_orders': recent_orders,
        'total_order_value': total_order_value,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='SupplierDashboard',
        description="Viewed supplier dashboard",
        request=request
    )
    
    return render(request, 'inventory/supplier_dashboard.html', context)


@login_required
@supplier_required
def supplier_orders(request):
    """
    List all orders for this supplier
    """
    supplier = request.user.supplier
    status_filter = request.GET.get('status', '')
    
    orders = PurchaseOrder.objects.filter(supplier=supplier)
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'supplier': supplier,
    }
    
    return render(request, 'inventory/supplier_orders.html', context)


@login_required
@supplier_required
def supplier_order_detail(request, order_id):
    """
    View order details (supplier view)
    """
    supplier = request.user.supplier
    order = get_object_or_404(PurchaseOrder, id=order_id, supplier=supplier)
    
    # Generate QR code image
    qr_code_image = PurchaseOrderService.generate_qr_code_image(order.qr_code)
    
    # Get order items
    order_items = order.order_items.select_related('item').all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'qr_code_image': qr_code_image,
        'supplier': supplier,
    }
    
    log_user_action(
        user=request.user,
        action_type='read',
        target_model='PurchaseOrder',
        target_id=order_id,
        description=f"Supplier viewed purchase order {order.order_no}",
        request=request
    )
    
    return render(request, 'inventory/supplier_order_detail.html', context)


@login_required
@supplier_required
def supplier_order_approve(request, order_id):
    """
    Supplier approves purchase order with pricing and delivery date
    """
    supplier = request.user.supplier
    order = get_object_or_404(PurchaseOrder, id=order_id, supplier=supplier)
    
    if not order.can_be_approved():
        messages.error(request, f"Purchase order cannot be approved. Current status: {order.get_status_display()}")
        return redirect('inventory:supplier_order_detail', order_id=order_id)
    
    order_items = order.order_items.all()
    
    if request.method == 'POST':
        form = PurchaseOrderApproveForm(request.POST, order_items=order_items)
        if form.is_valid():
            try:
                # Update item prices from supplier
                item_prices = form.get_item_prices()
                total_amount = Decimal('0')
                
                for po_item in order_items:
                    price_key = str(po_item.id)
                    if price_key in item_prices:
                        po_item.unit_price = item_prices[price_key]
                        po_item.save()
                        total_amount += po_item.subtotal()
                
                # Update total amount
                order.total_amount = total_amount
                order.save()
                
                # Approve order
                PurchaseOrderService.approve_purchase_order(
                    po=order,
                    supplier_notes=form.cleaned_data.get('supplier_notes'),
                    expected_delivery_date=form.cleaned_data['expected_delivery_date']
                )
                
                log_user_action(
                    user=request.user,
                    action_type='update',
                    target_model='PurchaseOrder',
                    target_id=order_id,
                    description=f"Supplier approved purchase order {order.order_no} with total amount ₱{total_amount}",
                    request=request
                )
                
                messages.success(request, f"Purchase order {order.order_no} approved successfully with total amount ₱{total_amount:,.2f}")
                
                # TODO: Send email notification to customer
                
                return redirect('inventory:supplier_order_detail', order_id=order_id)
            except Exception as e:
                messages.error(request, f"Error approving purchase order: {str(e)}")
    else:
        form = PurchaseOrderApproveForm(
            initial={'expected_delivery_date': order.expected_delivery_date},
            order_items=order_items
        )
    
    context = {
        'form': form,
        'order': order,
        'order_items': order_items,
        'supplier': supplier,
        'title': f'Approve Purchase Order: {order.order_no}',
    }
    
    return render(request, 'inventory/supplier_order_approve.html', context)


@login_required
@supplier_required
def supplier_order_ship(request, order_id):
    """
    Supplier marks order as shipped
    """
    supplier = request.user.supplier
    order = get_object_or_404(PurchaseOrder, id=order_id, supplier=supplier)
    
    if not order.can_be_shipped():
        messages.error(request, f"Purchase order cannot be shipped. Current status: {order.get_status_display()}")
        return redirect('inventory:supplier_order_detail', order_id=order_id)
    
    if request.method == 'POST':
        try:
            PurchaseOrderService.ship_purchase_order(order)
            
            log_user_action(
                user=request.user,
                action_type='update',
                target_model='PurchaseOrder',
                target_id=order_id,
                description=f"Supplier marked purchase order {order.order_no} as shipped",
                request=request
            )
            
            messages.success(request, f"Purchase order {order.order_no} marked as shipped.")
            
            # TODO: Send email notification to customer
            
        except Exception as e:
            messages.error(request, f"Error shipping purchase order: {str(e)}")
    
    return redirect('inventory:supplier_order_detail', order_id=order_id)


# Supplier Login View
def supplier_login(request):
    """
    Separate login page for suppliers
    """
    if request.user.is_authenticated:
        if request.user.is_supplier_user():
            return redirect('inventory:supplier_dashboard')
        else:
            return redirect('inventory:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_supplier_user():
                login(request, user)
                log_user_action(
                    user=user,
                    action_type='login',
                    target_model='User',
                    description=f"Supplier user logged in",
                    request=request
                )
                messages.success(request, f"Welcome back, {user.supplier.name}!")
                return redirect('inventory:supplier_dashboard')
            else:
                messages.error(request, "This account is not a supplier account. Please use the regular login.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'inventory/supplier_login.html')


@login_required
@permission_required('inventory_read')
def expiration_tracker(request):
    """View to track ingredient expiration dates"""
    from datetime import timedelta
    
    today = timezone.now().date()
    
    # Get all stock lots with expiration dates
    all_lots_with_expiry = StockLot.objects.filter(
        qty__gt=0,
        expires_at__isnull=False
    ).select_related('item').order_by('expires_at')
    
    # Expired lots
    expired_lots = []
    for lot in all_lots_with_expiry:
        if lot.expires_at < today:
            lot.is_expired = True
            lot.days_overdue = (today - lot.expires_at).days
            expired_lots.append(lot)
    
    # Expiring soon (within 7 days)
    expiring_soon_date = today + timedelta(days=7)
    expiring_soon_lots = []
    for lot in all_lots_with_expiry:
        if today <= lot.expires_at <= expiring_soon_date:
            lot.is_expiring_soon = True
            lot.days_left = (lot.expires_at - today).days
            expiring_soon_lots.append(lot)
    
    # All lots (including those without expiry)
    all_lots = StockLot.objects.filter(qty__gt=0).select_related('item').order_by('-received_at')
    
    # Add status flags to all lots
    for lot in all_lots:
        if lot.expires_at:
            if lot.expires_at < today:
                lot.is_expired = True
                lot.is_expiring_soon = False
            elif lot.expires_at <= expiring_soon_date:
                lot.is_expired = False
                lot.is_expiring_soon = True
            else:
                lot.is_expired = False
                lot.is_expiring_soon = False
        else:
            lot.is_expired = False
            lot.is_expiring_soon = False
    
    # Fresh stock count
    fresh_count = all_lots.count() - len(expired_lots) - len(expiring_soon_lots)
    
    context = {
        'expired_lots': expired_lots,
        'expiring_soon_lots': expiring_soon_lots,
        'all_lots': all_lots,
        'expired_count': len(expired_lots),
        'expiring_soon_count': len(expiring_soon_lots),
        'fresh_count': fresh_count,
    }
    
    return render(request, 'inventory/expiration_tracker.html', context)