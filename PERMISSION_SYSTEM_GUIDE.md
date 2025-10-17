# Permission-Based Navigation System

## Overview
The system now supports **granular permission management** for staff users. Admins can grant specific permissions to staff members, which controls what navigation items and features they can access.

## Permission Types

### Available Permissions:
1. **`inventory_read`** - Read Inventory
   - View inventory dashboard
   - View items list
   - View suppliers
   - View recipes
   
2. **`inventory_write`** - Write Inventory
   - Create/edit items
   - Create/edit purchase orders
   - Manage stock movements
   
3. **`inventory_delete`** - Delete Inventory
   - Delete items
   - Delete purchase orders
   
4. **`reports_read`** - Read Reports
   - View stock reports
   - View consumption reports
   - View analytics
   
5. **`reports_write`** - Write Reports
   - Generate custom reports
   - Export reports
   
6. **`user_read`** - Read Users
   - View user list
   - View user details
   
7. **`user_write`** - Write Users (Admin only)
   - Create/edit users
   - Manage user permissions
   
8. **`user_delete`** - Delete Users (Super Admin only)
   - Delete user accounts
   
9. **`settings_read`** - Read Settings
   - View system settings
   
10. **`settings_write`** - Write Settings
    - Modify system settings

## Navigation Access Control

### Staff Users (Role: `staff`)
**Default Access:**
- ✅ Dashboard (always visible)
- ✅ My Attendance (always visible)

**Permission-Based Access:**
- 📦 **Inventory** - Requires `inventory_read`
- 🛍️ **Items** - Requires `inventory_read`
- 🛒 **Purchase Orders** - Requires `inventory_write`
- 🚚 **Suppliers** - Requires `inventory_read`
- 📖 **Recipes** - Requires `inventory_read`
- 📊 **Reports** - Requires `reports_read`

### Admin Users (Role: `admin`)
- ✅ **Full access** to all features except:
  - Cannot grant `user_write` or `user_delete` permissions
  - Cannot delete users

### Super Admin Users (Role: `super_admin`)
- ✅ **Complete access** to all features
- ✅ Can grant any permission
- ✅ Can manage all users

## How to Grant Permissions

### Method 1: Through Django Admin
1. Log in to Django Admin (`/admin/`)
2. Go to **User Accesses**
3. Click **Add User Access**
4. Select:
   - **User**: The staff member
   - **Permission Type**: The permission to grant
   - **Granted By**: Automatically set to current admin
   - **Expires At**: Optional expiration date
   - **Is Active**: Check to activate
5. Click **Save**

### Method 2: Through User Detail Page
1. Go to **Team** → Select a staff user
2. Click **Manage Permissions**
3. Check the permissions you want to grant
4. Click **Save Permissions**

### Method 3: Programmatically
```python
from inventory.models import User, UserAccess

# Get the staff user and admin
staff_user = User.objects.get(username='john_staff')
admin_user = User.objects.get(username='admin')

# Grant inventory read permission
UserAccess.objects.create(
    user=staff_user,
    permission_type='inventory_read',
    granted_by=admin_user,
    is_active=True
)

# Grant multiple permissions
permissions = ['inventory_read', 'inventory_write', 'reports_read']
for perm in permissions:
    UserAccess.objects.get_or_create(
        user=staff_user,
        permission_type=perm,
        defaults={'granted_by': admin_user, 'is_active': True}
    )
```

## Permission Checking in Code

### In Templates
```django
{% if user.has_permission('inventory_read') %}
    <a href="{% url 'inventory:item_list' %}">View Items</a>
{% endif %}
```

### In Views
```python
from django.shortcuts import redirect
from django.contrib import messages

def some_view(request):
    if not request.user.has_permission('inventory_write'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('inventory:dashboard')
    
    # Continue with view logic
    ...
```

### Using Decorator
```python
from inventory.security import permission_required

@login_required
@permission_required('inventory_write')
def create_item(request):
    # Only users with inventory_write permission can access
    ...
```

## Example Scenarios

### Scenario 1: Warehouse Staff
**Role:** Staff  
**Permissions Needed:**
- `inventory_read` - To view items and stock levels
- `inventory_write` - To receive stock and update quantities

**Navigation Visible:**
- Dashboard
- Inventory
- Items
- Purchase Orders
- Suppliers
- Recipes
- My Attendance

### Scenario 2: Sales Staff
**Role:** Staff  
**Permissions Needed:**
- `inventory_read` - To check product availability
- `reports_read` - To view sales reports

**Navigation Visible:**
- Dashboard
- Inventory
- Items
- Suppliers
- Recipes
- Reports
- My Attendance

### Scenario 3: Basic Staff (No Inventory Access)
**Role:** Staff  
**Permissions Needed:**
- None (just attendance tracking)

**Navigation Visible:**
- Dashboard
- My Attendance

### Scenario 4: Inventory Manager (Staff with elevated permissions)
**Role:** Staff  
**Permissions Needed:**
- `inventory_read`
- `inventory_write`
- `inventory_delete`
- `reports_read`
- `reports_write`

**Navigation Visible:**
- Dashboard
- Inventory
- Items
- Purchase Orders
- Suppliers
- Recipes
- Reports
- My Attendance

## Permission Expiration

Permissions can have expiration dates:

```python
from datetime import timedelta
from django.utils import timezone

# Grant permission that expires in 30 days
UserAccess.objects.create(
    user=staff_user,
    permission_type='inventory_write',
    granted_by=admin_user,
    expires_at=timezone.now() + timedelta(days=30),
    is_active=True
)
```

The system automatically checks if permissions are expired using the `is_expired()` method.

## Security Features

### 1. Role-Based Defaults
- **Admin & Super Admin**: Have all permissions by default
- **Staff**: Need explicit permission grants
- **Supplier**: No inventory permissions (only view their orders)

### 2. Permission Hierarchy
- Only **Admin** or **Super Admin** can grant permissions
- Only **Super Admin** can grant `user_write` and `user_delete`
- Validation is enforced at the model level

### 3. Audit Trail
All permission grants are logged with:
- Who granted the permission
- When it was granted
- Expiration date (if any)
- Active status

## Testing Permissions

### Test Script
```python
# Run in Django shell: python manage.py shell

from inventory.models import User

# Get a staff user
staff = User.objects.get(username='john_staff')

# Check permissions
print(f"Has inventory_read: {staff.has_permission('inventory_read')}")
print(f"Has inventory_write: {staff.has_permission('inventory_write')}")
print(f"Has reports_read: {staff.has_permission('reports_read')}")

# List all active permissions
for access in staff.user_accesses.filter(is_active=True):
    print(f"- {access.get_permission_type_display()}")
```

## Best Practices

1. **Principle of Least Privilege**: Only grant permissions that are necessary for the user's role
2. **Regular Audits**: Periodically review and revoke unnecessary permissions
3. **Use Expiration Dates**: For temporary access, always set expiration dates
4. **Document Permissions**: Keep track of why specific permissions were granted
5. **Test Access**: After granting permissions, test that the user can access the intended features

## Troubleshooting

### Staff user can't see navigation items
**Check:**
1. User role is set to `staff`
2. Required permissions are granted and active
3. Permissions haven't expired
4. User has logged out and back in (to refresh session)

### Permission grant fails
**Common Issues:**
1. Non-admin trying to grant permissions
2. Admin trying to grant `user_write` or `user_delete` (only Super Admin can)
3. Duplicate permission (user already has that permission)

### Navigation not updating
**Solution:**
- Clear browser cache
- Log out and log back in
- Check browser console for JavaScript errors

---

**Last Updated**: October 17, 2025  
**System Version**: 1.0  
**Django Version**: 5.1.3
