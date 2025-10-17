# 📸 Visual Setup Guide - Screenshots & Instructions

## For Admins: How to See Purchase Orders & Add Suppliers

---

## ✅ FIXED: Purchase Orders Now Visible!

### Your Navigation Menu Now Shows:

```
┌───────────────────────────────────┐
│  INVENTRA                         │
│  ══════════                       │
│                                   │
│  🏠 Dashboard                     │
│  📦 Inventory                     │
│  🛍️ Items                         │
│  🔄 Stock Operations              │
│  🛒 Purchase Orders  ← NEW!       │
│  🚚 Suppliers                     │
│  📖 Recipes                       │
│  📊 Reports                       │
│                                   │
│  (Admin-only items below)         │
│  👥 Team                          │
│  📅 Attendance                    │
│  📋 Audit Logs                    │
│  ⚙️  Settings                     │
└───────────────────────────────────┘
```

**Click "Purchase Orders" to see all purchase orders!**

---

## 🔑 Admin Panel Guide

### Where is the Admin Panel?

```
URL: /admin/
or
URL: http://localhost:8000/admin/

Login with your admin credentials
```

### What You'll See:

```
╔════════════════════════════════════════════════════════╗
║         Django Administration                          ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  AUTHENTICATION AND AUTHORIZATION                      ║
║  ├─ Groups                                             ║
║  └─ Users  ← Click here for Step 2                    ║
║                                                        ║
║  INVENTORY                                             ║
║  ├─ Audit logs                                         ║
║  ├─ Items                                              ║
║  ├─ Purchase order items                               ║
║  ├─ Purchase orders                                    ║
║  ├─ Recipe items                                       ║
║  ├─ Recipes                                            ║
║  ├─ Stock lots                                         ║
║  ├─ Stock movements                                    ║
║  ├─ Suppliers  ← Click here for Step 1                ║
║  ├─ User accesses                                      ║
║  └─ User links                                         ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 📝 Step-by-Step with Visual Guide

### STEP 1: Create Supplier (Company Info)

#### 1.1 Navigate to Suppliers

```
Admin Panel Home
    │
    ├─> Scroll to "INVENTORY" section
    │
    └─> Click "Suppliers"
        │
        └─> You'll see supplier list
            │
            └─> Click "ADD SUPPLIER +" (green button, top right)
```

#### 1.2 Fill Supplier Form

```
╔════════════════════════════════════════════════════════╗
║  Add supplier                                          ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Name: [________________________] * Required           ║
║        Example: ABC Ingredients Co.                    ║
║                                                        ║
║  Contact person: [________________________]            ║
║                  Example: Juan Dela Cruz               ║
║                                                        ║
║  Phone: [________________________]                     ║
║         Example: +63 917 123 4567                      ║
║                                                        ║
║  Email: [________________________]                     ║
║         Example: orders@abcingredients.com             ║
║                                                        ║
║  Address: [_____________________]                      ║
║           [_____________________]                      ║
║           [_____________________]                      ║
║           Example: 123 Supply Street                   ║
║                    Manila, Philippines                 ║
║                                                        ║
║  ☑ Is active (MUST CHECK THIS!)                       ║
║                                                        ║
║  [Save and add another]  [Save and continue editing]  ║
║  [SAVE] ← Click this                                   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

#### 1.3 Verify Supplier Created

```
After saving, you should see:

╔════════════════════════════════════════════════════════╗
║  ✅ The supplier "ABC Ingredients Co." was added      ║
║     successfully.                                      ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Select supplier to change                             ║
║  ┌──────────────────────────────────────────────────┐ ║
║  │ 🔍 Search: [____________]                        │ ║
║  │                                                   │ ║
║  │ NAME              | CONTACT | PHONE | ACTIVE     │ ║
║  │ ABC Ingredients   | Juan... | +63.. | ✓ Yes     │ ║
║  │                                                   │ ║
║  └──────────────────────────────────────────────────┘ ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

✅ Supplier record created!
```

---

### STEP 2: Create Supplier User Account

#### 2.1 Navigate to Users

```
Admin Panel Home
    │
    ├─> Click "Home" link (top left)
    │
    ├─> Scroll to "AUTHENTICATION AND AUTHORIZATION"
    │
    └─> Click "Users"
        │
        └─> You'll see user list
            │
            └─> Click "ADD USER +" (green button, top right)
```

#### 2.2 Fill User Form - Page 1

```
╔════════════════════════════════════════════════════════╗
║  Add user                                              ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Username: [________________________] * Required       ║
║            Example: abc_supplier                       ║
║            Tip: Use {name}_supplier format             ║
║                                                        ║
║  Password: [________________________] * Required       ║
║            Example: SecurePass123!                     ║
║            (Give this to supplier)                     ║
║                                                        ║
║  Password confirmation: [____________] * Required      ║
║                         (Same password)                ║
║                                                        ║
║  [SAVE] ← Click this                                   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

#### 2.3 Fill User Form - Page 2 (After clicking Save)

```
╔════════════════════════════════════════════════════════╗
║  Change user: abc_supplier                             ║
╠════════════════════════════════════════════════════════╝

  PERSONAL INFO
  ┌──────────────────────────────────────────────────┐
  │ First name: [_______________]                    │
  │             Example: Juan                        │
  │                                                   │
  │ Last name:  [_______________]                    │
  │             Example: Dela Cruz                   │
  │                                                   │
  │ Email address: [_______________] * Required      │
  │                Example: orders@abcingredients.com│
  │                                                   │
  │ Phone number: [_______________]                  │
  │               Example: +63 917 123 4567          │
  │                                                   │
  │ Address: [_____________________]                 │
  │          [_____________________]                 │
  └──────────────────────────────────────────────────┘

  PERMISSIONS (SCROLL DOWN - CRITICAL SECTION!)
  ┌──────────────────────────────────────────────────┐
  │ Role: [Supplier        ▼] * Required             │
  │       ↑ SELECT "Supplier" - CRITICAL!            │
  │                                                   │
  │       Options:                                    │
  │       - Super Admin                               │
  │       - Admin                                     │
  │       - Staff                                     │
  │       - Supplier  ← CHOOSE THIS!                 │
  │                                                   │
  │ Supplier: [ABC Ingredients Co. ▼] * CRITICAL!    │
  │           ↑ MUST SELECT THE SUPPLIER!            │
  │           This dropdown shows all suppliers       │
  │                                                   │
  │ ☑ Active (MUST CHECK!)                           │
  │                                                   │
  │ ☐ Staff status                                    │
  │ ☐ Superuser status                                │
  └──────────────────────────────────────────────────┘

  [Save and continue editing]  [Save and add another]
  [SAVE] ← Click this

✅ User created and linked to supplier!
```

---

## 🎯 Visual Verification

### After Creating User, You Should See:

```
╔════════════════════════════════════════════════════════╗
║  ✅ The user "abc_supplier" was changed successfully. ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Select user to change                                 ║
║  ┌──────────────────────────────────────────────────┐ ║
║  │ 🔍 Search: [____________]                        │ ║
║  │                                                   │ ║
║  │ USERNAME      | EMAIL           | ROLE           │ ║
║  │ admin         | admin@...       | Super Admin    │ ║
║  │ abc_supplier  | orders@abc...   | Supplier ✓     │ ║
║  │                                                   │ ║
║  └──────────────────────────────────────────────────┘ ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

✅ User created with Supplier role!
```

---

## 🧪 Testing the Setup

### Test 1: Verify Supplier Can Login

```
1. Open new browser window (incognito mode)

2. Go to: /supplier/login/

3. You should see:
   ╔═══════════════════════════════════╗
   ║     🚚 Supplier Portal            ║
   ║   BIT Management System           ║
   ╠═══════════════════════════════════╣
   ║                                   ║
   ║  👤 Username: [_________]         ║
   ║  🔒 Password: [_________]         ║
   ║                                   ║
   ║  [Login to Supplier Portal]       ║
   ║                                   ║
   ║  OR                               ║
   ║  🏢 Staff/Admin Login             ║
   ╚═══════════════════════════════════╝

4. Enter:
   Username: abc_supplier
   Password: SecurePass123!

5. Click Login

6. Should see:
   ╔═══════════════════════════════════╗
   ║  Supplier Portal Dashboard        ║
   ║  Welcome, ABC Ingredients Co.!    ║
   ╠═══════════════════════════════════╣
   ║                                   ║
   ║  📊 Pending Orders: 0             ║
   ║  📊 Approved Orders: 0            ║
   ║  📊 Shipped Orders: 0             ║
   ║  📊 Received Orders: 0            ║
   ║                                   ║
   ╚═══════════════════════════════════╝

✅ If you see this = SUCCESS!
```

### Test 2: Verify Admin Can See Purchase Orders

```
1. Login as Admin: /login/

2. Look at left sidebar menu

3. You should see:
   ┌─────────────────────┐
   │ ...                 │
   │ Stock Operations    │
   │ Purchase Orders ←   │ Should see this!
   │ Suppliers           │
   │ ...                 │
   └─────────────────────┘

4. Click "Purchase Orders"

5. Should go to: /purchase-orders/

6. Should see:
   ╔═══════════════════════════════════╗
   ║  Purchase Orders                  ║
   ╠═══════════════════════════════════╣
   ║                                   ║
   ║  [Create PO] [Scan & Receive]     ║
   ║                                   ║
   ║  Statistics cards...              ║
   ║  Order list...                    ║
   ║                                   ║
   ╚═══════════════════════════════════╝

✅ If you see this = SUCCESS!
```

---

## 📋 Complete Visual Workflow

### Adding Supplier from Start to Finish

```
START
  │
  ▼
┌─────────────────────────────────┐
│ 1. Open /admin/                 │
│    Login with admin credentials │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 2. Admin Panel Home             │
│    ┌─────────────────────────┐  │
│    │ INVENTORY               │  │
│    │ ├─ Suppliers  ← CLICK   │  │
│    └─────────────────────────┘  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 3. Suppliers List               │
│    [ADD SUPPLIER +] ← CLICK     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 4. Supplier Form                │
│    Name: ABC Ingredients Co.    │
│    Contact: Juan Dela Cruz      │
│    Phone: +63 917 123 4567      │
│    Email: orders@abc.com        │
│    Address: 123 Supply St       │
│    ☑ Is active                  │
│    [SAVE] ← CLICK               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 5. Success Message              │
│    ✅ Supplier added            │
│    ┌─────────────────────────┐  │
│    │ ABC Ingredients Co. ✓   │  │
│    └─────────────────────────┘  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 6. Back to Admin Home           │
│    Click "Home" (top left)      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 7. Admin Panel Home             │
│    ┌─────────────────────────┐  │
│    │ AUTHENTICATION...       │  │
│    │ ├─ Users  ← CLICK       │  │
│    └─────────────────────────┘  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 8. Users List                   │
│    [ADD USER +] ← CLICK         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 9. User Form - Page 1           │
│    Username: abc_supplier       │
│    Password: SecurePass123!     │
│    Password (again): Same       │
│    [SAVE] ← CLICK               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 10. User Form - Page 2          │
│     First name: Juan            │
│     Last name: Dela Cruz        │
│     Email: orders@abc.com       │
│     ──────────────────────      │
│     Role: [Supplier ▼] ← SET!   │
│     Supplier: [ABC... ▼] ← LINK!│
│     ☑ Active ← CHECK!           │
│     [SAVE] ← CLICK              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 11. Success!                    │
│     ✅ User created             │
│     ✅ Linked to supplier       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 12. Test Login                  │
│     Open: /supplier/login/      │
│     Login: abc_supplier         │
│     Should see dashboard ✓      │
└────────────┬────────────────────┘
             │
             ▼
          ✅ DONE!
```

---

## 🎯 Finding the Supplier Dropdown

### Where is the Supplier Field?

When editing a user account, scroll down to find:

```
╔════════════════════════════════════════════════════════╗
║  Change user                                           ║
╠════════════════════════════════════════════════════════╣
║  (Scroll down past personal info...)                   ║
║  ...                                                   ║
║  ...                                                   ║
║  ...                                                   ║
║                                                        ║
║  Role: [Supplier ▼]                                    ║
║                                                        ║
║  Phone number: [_________]                             ║
║                                                        ║
║  Address: [________]                                   ║
║                                                        ║
║  Birthday: [________]                                  ║
║                                                        ║
║  ☑ Active                                              ║
║                                                        ║
║  Supplier: [ABC Ingredients Co. ▼]  ← HERE IT IS!      ║
║            ↑ This is what you're looking for!          ║
║            Click dropdown to see all suppliers         ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

**It's near the bottom of the form, after the Role field!**

---

## 🔍 How to Verify Everything

### Verification Checklist with Visuals

#### ✅ Check 1: Supplier Record Exists

```
Admin → Suppliers → Should see:

┌──────────────────────────────────────────┐
│ NAME               | CONTACT  | ACTIVE   │
├──────────────────────────────────────────┤
│ ABC Ingredients Co.| Juan...  | ✓ Yes    │
└──────────────────────────────────────────┘

✅ If you see your supplier = Good!
```

#### ✅ Check 2: User Account Exists

```
Admin → Users → Should see:

┌──────────────────────────────────────────┐
│ USERNAME      | EMAIL        | ROLE      │
├──────────────────────────────────────────┤
│ abc_supplier  | orders@...   | Supplier  │
└──────────────────────────────────────────┘

✅ If you see "Supplier" role = Good!
```

#### ✅ Check 3: User Linked to Supplier

```
Admin → Users → Click "abc_supplier" → Should see:

Role: Supplier ✓
Supplier: ABC Ingredients Co. ✓
Active: ✓ Yes

✅ If all three checked = Perfect!
```

#### ✅ Check 4: Supplier Can Login

```
/supplier/login/ → Login → Should see:

╔════════════════════════════════════════╗
║ Supplier Portal Dashboard              ║
║ Welcome, ABC Ingredients Co.!  ← Shows!║
╠════════════════════════════════════════╣
║ Statistics...                          ║
╚════════════════════════════════════════╝

✅ If company name shows = Success!
```

---

## 🎊 Visual Summary

### Complete Setup in One View

```
┌─────────────────────────────────────────────────────────┐
│                   COMPLETE SETUP                         │
└─────────────────────────────────────────────────────────┘

STEP 1: Supplier Record
┌──────────────────────┐
│ ABC Ingredients Co.  │
│ Contact: Juan        │
│ Email: orders@...    │
│ ☑ Active             │
└──────────────────────┘
         │
         │ Creates
         ▼
DATABASE: supplier table
         │
         │
STEP 2: User Account    │
┌──────────────────────┐│
│ Username: abc_supplier│
│ Role: Supplier       ││
│ Supplier: ───────────┘│ ← Links here!
│ ☑ Active             │
└──────────────────────┘
         │
         │ Creates
         ▼
DATABASE: user table
         │
         │ OneToOne relationship
         ▼
    Supplier Portal Access!
    
Result:
├─ User can login at /supplier/login/
├─ See dashboard for ABC Ingredients
├─ View ABC's purchase orders only
└─ Approve orders with pricing
```

---

## 🎉 You're Ready!

### What You Can Do Now

✅ **See Purchase Orders**: Click menu item  
✅ **Create Suppliers**: In admin panel  
✅ **Create Supplier Accounts**: Link to suppliers  
✅ **Test Workflow**: End-to-end  

### Where to Go

| Task | URL |
|------|-----|
| Admin Panel | `/admin/` |
| Add Supplier | `/admin/` → Suppliers → Add |
| Add User | `/admin/` → Users → Add |
| See Purchase Orders | Click menu or `/purchase-orders/` |
| Test Supplier Login | `/supplier/login/` |

---

**Visual Guide Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: ✅ Complete

🎊 **Everything is clear and ready to use!** 🎊

