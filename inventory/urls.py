from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'inventory'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
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
]
