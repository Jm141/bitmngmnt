# 🚀 Quick Setup Guide - Purchase Orders & Supplier Portal

## For Administrators

This is your quick reference for setting up the system and adding suppliers.

---

## ✅ Navigation Menu Added!

**Purchase Orders menu is now visible to all Admin users!**

Location: In the left sidebar menu  
Icon: 🛒 Shopping Cart  
Link: Takes you to Purchase Orders list  

---

## 📋 Adding Suppliers - Step by Step

### STEP 1: Create Supplier Record (Company Info)

```
1. Login to Admin Panel
   └─> URL: /admin/
   └─> Use your admin credentials

2. Navigate to Suppliers
   └─> Look for "INVENTORY" section
   └─> Click "Suppliers"

3. Click "Add Supplier" (green + button)

4. Fill in the form:
   
   ┌──────────────────────────────────────────┐
   │ Name: *                                  │
   │ └─> ABC Ingredients Co.                  │
   │                                          │
   │ Contact Person:                          │
   │ └─> Juan Dela Cruz                       │
   │                                          │
   │ Phone:                                   │
   │ └─> +63 917 123 4567                     │
   │                                          │
   │ Email:                                   │
   │ └─> orders@abcingredients.com            │
   │                                          │
   │ Address:                                 │
   │ └─> 123 Supply St, Manila                │
   │                                          │
   │ ☑ Is active (Check this!)                │
   └──────────────────────────────────────────┘

5. Click "Save"

✅ Supplier company record created!
```

### STEP 2: Create Supplier User Account (Login Access)

```
1. Still in Admin Panel
   └─> Click "Home" (top left)

2. Navigate to Users
   └─> Look for "AUTHENTICATION AND AUTHORIZATION"
   └─> Click "Users"

3. Click "Add User +" (green button)

4. Fill in BASIC INFO:
   
   ┌──────────────────────────────────────────┐
   │ Username: *                              │
   │ └─> abc_supplier                         │
   │     (Tip: use supplier_name format)      │
   │                                          │
   │ Password: *                              │
   │ └─> SecurePassword123!                   │
   │     (Give this to supplier)              │
   │                                          │
   │ Password confirmation: *                 │
   │ └─> SecurePassword123!                   │
   │     (Same password)                      │
   └──────────────────────────────────────────┘

5. Fill in PERSONAL INFO (scroll down):
   
   ┌──────────────────────────────────────────┐
   │ First name:                              │
   │ └─> Juan                                 │
   │                                          │
   │ Last name:                               │
   │ └─> Dela Cruz                            │
   │                                          │
   │ Email address: *                         │
   │ └─> orders@abcingredients.com            │
   └──────────────────────────────────────────┘

6. Set ROLE & SUPPLIER LINK (CRITICAL!):
   
   ┌──────────────────────────────────────────┐
   │ Role: *                                  │
   │ └─> [Supplier ▼] ← SELECT "Supplier"!   │
   │                                          │
   │ Supplier: *                              │
   │ └─> [ABC Ingredients Co. ▼]              │
   │     ↑ MUST SELECT THE SUPPLIER!          │
   │     This links user to company!          │
   │                                          │
   │ ☑ Active (Check this!)                   │
   └──────────────────────────────────────────┘

7. Click "Save"

✅ Supplier user account created and linked!
```

### STEP 3: Verify & Test

```
1. Logout from admin

2. Go to Supplier Login
   └─> URL: /supplier/login/

3. Test the account:
   ├─ Username: abc_supplier
   ├─ Password: SecurePassword123!
   └─ Click "Login to Supplier Portal"

4. Should see:
   ├─ Supplier Dashboard
   ├─ Company name: "ABC Ingredients Co."
   ├─ Statistics (all 0 if no orders yet)
   └─> ✅ If you see this = SUCCESS!

5. Logout and login back as admin
```

---

## ⚠️ CRITICAL: The Supplier Link!

### This is the MOST IMPORTANT part!

```
❌ WRONG (User not linked):
┌─────────────────┐
│ User: abc_supplier │
│ Role: Supplier  │
│ Supplier: (blank) │  ← NOT LINKED!
└─────────────────┘
Problem: User can login but sees no orders!

✅ CORRECT (User linked):
┌─────────────────────────┐
│ User: abc_supplier      │
│ Role: Supplier          │
│ Supplier: ABC Ingredients│ ← LINKED!
└─────────────────────────┘
Result: User sees ABC's orders!
```

**The Supplier dropdown links the user account to the supplier company!**

---

## 🎯 Full Example

### Adding "Fresh Bakery Supplies"

```
STEP 1: Create Supplier Company
════════════════════════════════════════
Admin Panel → Suppliers → Add Supplier

Name: Fresh Bakery Supplies
Contact Person: Maria Santos
Phone: +63 2 8555 1234
Email: orders@freshbakery.com
Address: 456 Market Ave, Quezon City
☑ Is active

[Save] → ✅ Supplier created!

STEP 2: Create Login Account
════════════════════════════════════════
Admin Panel → Users → Add User

USERNAME & PASSWORD:
├─ Username: fresh_bakery
├─ Password: BakerySupp2025!
└─ Password confirmation: BakerySupp2025!

PERSONAL INFO:
├─ First name: Maria
├─ Last name: Santos
└─ Email: orders@freshbakery.com

ROLE & LINK (CRITICAL!):
├─ Role: Supplier ← MUST select!
├─ Supplier: Fresh Bakery Supplies ← MUST link!
└─ ☑ Active

[Save] → ✅ User created and linked!

STEP 3: Give to Supplier
════════════════════════════════════════
Email to: orders@freshbakery.com

Hi Maria,

Your supplier portal access:
URL: https://yoursite.com/supplier/login/
Username: fresh_bakery
Password: BakerySupp2025!

Login to view and approve orders!

STEP 4: Test
════════════════════════════════════════
└─> Login at /supplier/login/
    └─> See dashboard with "Fresh Bakery Supplies"
        ✅ Working!
```

---

## 🔍 How to Check If Purchase Orders Menu is Visible

### For Admin Users

When logged in as Admin, you should see in the left menu:

```
☐ Dashboard
☐ Inventory
☐ Items
☐ Stock Operations
☐ Purchase Orders ← Should see this!
☐ Suppliers
☐ Recipes
☐ Reports
☐ Team
☐ Attendance
```

If you DON'T see "Purchase Orders":

1. **Check you're logged in as Admin/Super Admin**
   - Staff users have limited menu
   
2. **Refresh the page** (Ctrl + F5)
   - Clear cache
   
3. **Check the base.html was updated**
   - Should have Purchase Orders menu item

---

## 🛠️ Troubleshooting

### "I don't see Purchase Orders in menu"

**Solution 1**: You might be logged in as Staff
- Staff have limited permissions
- Login as Admin or Super Admin

**Solution 2**: Clear browser cache
- Press Ctrl + F5 to hard refresh
- Or clear cookies/cache

**Solution 3**: Check your role
- Admin Panel → Users → Your user
- Verify Role = "Admin" or "Super Admin"

### "Supplier can't find their company in dropdown"

**Cause**: Supplier record not created yet

**Solution**:
- Do STEP 1 first (create supplier record)
- Make sure it's marked as "Active"
- Refresh user form
- Dropdown should now show the supplier

### "Supplier can login but sees no orders"

**Cause 1**: User not linked to supplier
**Solution**: Admin → Users → Edit user → Set Supplier field

**Cause 2**: No orders created yet
**Solution**: Create a test purchase order for that supplier

### "Getting permission errors"

**Cause**: Role not set correctly

**Solution**:
- Admin → Users → Edit user
- Change "Role" to "Supplier"
- Make sure "Supplier" field is also set
- Save

---

## 📊 Admin Access to Purchase Orders

### What Admins Can Do

✅ **View all purchase orders** (from all suppliers)  
✅ **Create purchase orders**  
✅ **Approve orders** (if needed to help)  
✅ **Mark as shipped** (if needed)  
✅ **Scan & receive orders**  
✅ **Cancel orders**  
✅ **View complete history**  
✅ **Filter and search**  

### How to Access

```
1. Login as Admin
   └─> /login/

2. See navigation menu
   └─> Click "Purchase Orders"
       └─> Goes to /purchase-orders/

3. You'll see:
   ├─ All purchase orders
   ├─ From all suppliers
   ├─ All statuses
   ├─ [Create Purchase Order] button
   └─> [Scan & Receive] button
```

---

## 📚 Complete Setup Checklist

### Initial System Setup

```
[ ] Admin Panel accessible (/admin/)
[ ] Purchase Orders menu visible
[ ] Can navigate to purchase orders page
[ ] Can click "Create Purchase Order"

For Each Supplier:
[ ] Create supplier company record
[ ] Verify supplier is active
[ ] Create user account
[ ] Set username
[ ] Set secure password
[ ] Set first & last name
[ ] Set email
[ ] Set role to "Supplier" ← CRITICAL!
[ ] Link to supplier record ← CRITICAL!
[ ] Set user as active
[ ] Test login at /supplier/login/
[ ] Verify dashboard shows
[ ] Send credentials to supplier

After Setup:
[ ] Create test purchase order
[ ] Verify supplier can see it
[ ] Supplier approves with pricing
[ ] Verify prices show for admin
[ ] Complete full workflow test
```

---

## 🎓 Training Notes

### For You (Admin)

**Remember**:
1. Create supplier company record FIRST
2. Then create user account SECOND
3. MUST link user to supplier
4. MUST set role to "Supplier"
5. Test before giving to supplier

### For Suppliers

**Tell them**:
1. Use the supplier login page (/supplier/login/)
2. NOT the regular staff login
3. They will see their company orders only
4. They provide pricing when approving
5. They set delivery dates

---

## 🎉 Quick Reference

### Key URLs

| Page | URL | Who Can Access |
|------|-----|----------------|
| Admin Panel | `/admin/` | Admin/Super Admin |
| Staff Login | `/login/` | Staff/Admin |
| Supplier Login | `/supplier/login/` | Suppliers only |
| Purchase Orders | `/purchase-orders/` | Admin/Staff |
| Supplier Portal | `/supplier/dashboard/` | Suppliers only |

### Creating Supplier Workflow

```
Admin Panel → Suppliers → Add
  ↓
Fill company info → Save
  ↓
Admin Panel → Users → Add
  ↓
Fill user info → Set Role: Supplier → Link to Supplier → Save
  ↓
Test login → Send credentials to supplier
  ↓
✅ Done!
```

---

## 💡 Pro Tips

1. **Username Convention**: Use `{supplier_name}_supplier` format
2. **Strong Passwords**: Mix letters, numbers, symbols
3. **Same Email**: Use same email in both records
4. **Test Immediately**: Login as supplier to verify
5. **Document**: Keep record of supplier credentials
6. **Security**: Send passwords securely (not plain email)

---

**Setup Guide Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: ✅ Ready to Use

🎊 **You can now add suppliers and see purchase orders!** 🎊

