"""
Script to update template paths in views.py after reorganizing templates into subdirectories
"""

import re

# Define the mapping of old paths to new paths
TEMPLATE_MAPPINGS = {
    # Auth templates
    "'inventory/login.html'": "'inventory/auth/login.html'",
    
    # Item templates
    "'inventory/item_list.html'": "'inventory/items/item_list.html'",
    "'inventory/item_detail.html'": "'inventory/items/item_detail.html'",
    "'inventory/item_form.html'": "'inventory/items/item_form.html'",
    
    # Purchase Order templates
    "'inventory/purchase_order_list.html'": "'inventory/purchase_orders/purchase_order_list.html'",
    "'inventory/purchase_order_detail.html'": "'inventory/purchase_orders/purchase_order_detail.html'",
    "'inventory/purchase_order_form.html'": "'inventory/purchase_orders/purchase_order_form.html'",
    "'inventory/purchase_order_receive.html'": "'inventory/purchase_orders/purchase_order_receive.html'",
    "'inventory/purchase_order_approve.html'": "'inventory/purchase_orders/purchase_order_approve.html'",
    "'inventory/purchase_order_scan.html'": "'inventory/purchase_orders/purchase_order_scan.html'",
    "'inventory/purchase_order_admin_approve.html'": "'inventory/purchase_orders/purchase_order_admin_approve.html'",
    "'inventory/purchase_order_admin_reject.html'": "'inventory/purchase_orders/purchase_order_admin_reject.html'",
    "'inventory/purchase_order_cancel.html'": "'inventory/purchase_orders/purchase_order_cancel.html'",
    
    # User templates
    "'inventory/user_list.html'": "'inventory/users/user_list.html'",
    "'inventory/user_detail.html'": "'inventory/users/user_detail.html'",
    "'inventory/user_form.html'": "'inventory/users/user_form.html'",
    "'inventory/user_confirm_delete.html'": "'inventory/users/user_confirm_delete.html'",
    "'inventory/user_permissions.html'": "'inventory/users/user_permissions.html'",
    "'inventory/attendance_dashboard.html'": "'inventory/users/attendance_dashboard.html'",
    "'inventory/admin_attendance_overview.html'": "'inventory/users/admin_attendance_overview.html'",
    
    # Production templates
    "'inventory/production_list.html'": "'inventory/production/production_list.html'",
    "'inventory/production_form.html'": "'inventory/production/production_form.html'",
    "'inventory/recipe_list.html'": "'inventory/production/recipe_list.html'",
    "'inventory/recipe_detail.html'": "'inventory/production/recipe_detail.html'",
    "'inventory/recipe_form.html'": "'inventory/production/recipe_form.html'",
    
    # Supplier templates
    "'inventory/supplier_list.html'": "'inventory/suppliers/supplier_list.html'",
    "'inventory/supplier_form.html'": "'inventory/suppliers/supplier_form.html'",
    "'inventory/supplier_dashboard.html'": "'inventory/suppliers/supplier_dashboard.html'",
    "'inventory/supplier_login.html'": "'inventory/suppliers/supplier_login.html'",
    "'inventory/supplier_orders.html'": "'inventory/suppliers/supplier_orders.html'",
    "'inventory/supplier_order_detail.html'": "'inventory/suppliers/supplier_order_detail.html'",
    "'inventory/supplier_order_approve.html'": "'inventory/suppliers/supplier_order_approve.html'",
    
    # Stock templates
    "'inventory/stock_receive.html'": "'inventory/stock/stock_receive.html'",
    "'inventory/stock_consume.html'": "'inventory/stock/stock_consume.html'",
    "'inventory/expiration_tracker.html'": "'inventory/stock/expiration_tracker.html'",
    
    # Report templates
    "'inventory/stock_report.html'": "'inventory/reports/stock_report.html'",
    "'inventory/audit_logs.html'": "'inventory/reports/audit_logs.html'",
}

def update_views_file():
    """Update the views.py file with new template paths"""
    views_path = r'c:\Users\User1\Desktop\caps\bitmngmnt\inventory\views.py'
    
    # Read the file
    with open(views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track changes
    changes_made = []
    
    # Replace each template path
    for old_path, new_path in TEMPLATE_MAPPINGS.items():
        if old_path in content:
            count = content.count(old_path)
            content = content.replace(old_path, new_path)
            changes_made.append(f"  ✓ {old_path} → {new_path} ({count} occurrences)")
    
    # Write the updated content back
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return changes_made

if __name__ == '__main__':
    print("Updating template paths in views.py...")
    print("=" * 70)
    
    changes = update_views_file()
    
    if changes:
        print(f"\n✅ Successfully updated {len(changes)} template paths:\n")
        for change in changes:
            print(change)
    else:
        print("\n⚠️  No changes were made. All paths may already be updated.")
    
    print("\n" + "=" * 70)
    print("Done!")
