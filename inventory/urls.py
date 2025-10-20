from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'inventory'

urlpatterns = [
    # Authentication URLs
    path('login/', views.unified_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inventory:login'), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/clock/', views.clock_event, name='clock_event'),
    
    # User Management URLs
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<uuid:user_id>/', views.user_detail, name='user_detail'),
    path('users/<uuid:user_id>/update/', views.user_update, name='user_update'),
    path('users/<uuid:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<uuid:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    path('users/<uuid:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    
    # Audit Logs
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Admin Attendance Overview
    path('attendance-overview/', views.admin_attendance_overview, name='admin_attendance_overview'),
    
    # Debug URL
    path('nav-debug/', views.nav_debug, name='nav_debug'),
    
    # Inventory Management URLs
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    
    # Items
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<uuid:item_id>/', views.item_detail, name='item_detail'),
    path('items/<uuid:item_id>/update/', views.item_update, name='item_update'),
    
    # Stock Operations
    path('stock/receive/', views.stock_receive, name='stock_receive'),
    path('stock/consume/', views.stock_consume, name='stock_consume'),
    path('api/item-lots/', views.api_item_lots, name='api_item_lots'),
    path('api/item-meta/', views.api_item_meta, name='api_item_meta'),
    path('production/', views.production_create, name='production_create'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    
    # Recipes
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/create/', views.recipe_create, name='recipe_create'),
    path('recipes/<uuid:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    
    # Reports
    path('reports/stock/', views.stock_report, name='stock_report'),
    
    # Expiration Tracker
    path('expiration-tracker/', views.expiration_tracker, name='expiration_tracker'),
    
    # Purchase Orders
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<uuid:order_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<uuid:order_id>/approve/', views.purchase_order_approve, name='purchase_order_approve'),
    path('purchase-orders/<uuid:order_id>/ship/', views.purchase_order_ship, name='purchase_order_ship'),
    path('purchase-orders/<uuid:order_id>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
    path('purchase-orders/<uuid:order_id>/cancel/', views.purchase_order_cancel, name='purchase_order_cancel'),
    path('purchase-orders/scan/receive/', views.purchase_order_scan_receive, name='purchase_order_scan_receive'),
    
    # Supplier Portal
    path('supplier/login/', views.supplier_login, name='supplier_login'),
    path('supplier/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),
    path('supplier/orders/', views.supplier_orders, name='supplier_orders'),
    path('supplier/orders/<uuid:order_id>/', views.supplier_order_detail, name='supplier_order_detail'),
    path('supplier/orders/<uuid:order_id>/approve/', views.supplier_order_approve, name='supplier_order_approve'),
    path('supplier/orders/<uuid:order_id>/ship/', views.supplier_order_ship, name='supplier_order_ship'),
]
