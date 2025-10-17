# 📘 How to Add Suppliers and Their Accounts

## Complete Step-by-Step Guide

This guide shows you exactly how to add suppliers to the system and create their login accounts.

---

## 🎯 Two-Step Process

```
STEP 1: Create Supplier Record (Company Information)
STEP 2: Create Supplier User Account (Login Access)
```

**Important**: You must do Step 1 first, then Step 2!

---

## STEP 1: Create Supplier Record

### What This Does
Creates the supplier company record (contact info, address, etc.)

### Instructions

#### Option A: Via Django Admin (Recommended)

```
1. Login to Admin Panel
   URL: /admin/
   Credentials: Your admin username/password

2. Find Suppliers Section
   ├─ Look for "INVENTORY" section
   └─ Click on "Suppliers"

3. Click "Add Supplier" Button
   (Top right corner)

4. Fill in Supplier Information:
   ┌──────────────────────────────────────────┐
   │ Name: * (Required)                       │
   │ └─> Example: "ABC Ingredients Co."       │
   │                                          │
   │ Contact Person: (Optional)               │
   │ └─> Example: "Juan Dela Cruz"           │
   │                                          │
   │ Phone: (Optional)                        │
   │ └─> Example: "+63 917 123 4567"         │
   │                                          │
   │ Email: (Optional but recommended)        │
   │ └─> Example: "orders@abcingredients.com"│
   │                                          │
   │ Address: (Optional)                      │
   │ └─> Example: "123 Main St, Manila"      │
   │                                          │
   │ ☑ Is active (Check this!)               │
   └──────────────────────────────────────────┘

5. Click "Save" Button

6. Success!
   ├─ Supplier record created
   ├─ You'll see it in the supplier list
   └─ Note the supplier name for Step 2
```

#### Option B: Via Application (If supplier_create view exists)

```
1. Login as Admin
   URL: /login/

2. Navigate to Suppliers
   Click: Suppliers menu item

3. Click "Create Supplier"

4. Fill same information as above

5. Submit
```

---

## STEP 2: Create Supplier User Account

### What This Does
Creates a login account that links to the supplier record

### Instructions

```
1. Login to Admin Panel
   URL: /admin/
   Credentials: Your admin username/password

2. Find Users Section
   ├─ Look for "AUTHENTICATION AND AUTHORIZATION"
   └─ Click on "Users"

3. Click "Add User+" Button
   (Top right corner - green button)

4. Fill in User Information:
   
   ┌──────────────────────────────────────────────┐
   │ BASIC INFORMATION                             │
   ├──────────────────────────────────────────────┤
   │                                              │
   │ Username: * (Required)                       │
   │ └─> Example: "abc_supplier"                  │
   │     Recommendation: {company_name}_supplier  │
   │                                              │
   │ Password: * (Required)                       │
   │ └─> Create a strong password                 │
   │     Example: "SecurePass123!"                │
   │                                              │
   │ Password confirmation: * (Required)          │
   │ └─> Re-enter the same password               │
   │                                              │
   ├──────────────────────────────────────────────┤
   │ PERSONAL INFO                                 │
   ├──────────────────────────────────────────────┤
   │                                              │
   │ First name:                                  │
   │ └─> Contact person's first name              │
   │     Example: "Juan"                          │
   │                                              │
   │ Last name:                                   │
   │ └─> Contact person's last name               │
   │     Example: "Dela Cruz"                     │
   │                                              │
   │ Email address: * (Required)                  │
   │ └─> Supplier email                           │
   │     Example: "orders@abcingredients.com"     │
   │                                              │
   ├──────────────────────────────────────────────┤
   │ PERMISSIONS (CRITICAL!)                       │
   ├──────────────────────────────────────────────┤
   │                                              │
   │ Role: * (Required)                           │
   │ └─> SELECT "Supplier" ← IMPORTANT!           │
   │     [v] Super Admin                          │
   │     [ ] Admin                                │
   │     [ ] Staff                                │
   │     [✓] Supplier ← MUST SELECT THIS!         │
   │                                              │
   │ Supplier: * (CRITICAL!)                      │
   │ └─> Select supplier from dropdown            │
   │     [ABC Ingredients Co. ▼] ← MUST LINK!     │
   │     This links the user to the supplier!     │
   │                                              │
   │ ☑ Active (Check this!)                       │
   │                                              │
   └──────────────────────────────────────────────┘

5. Scroll Down & Click "Save"

6. Success!
   ├─ Supplier user account created
   ├─ Linked to supplier record
   └─ Ready to login at /supplier/login/
```

---

## ⚠️ CRITICAL: The Link!

### Why You MUST Link User to Supplier

```
❌ WITHOUT Link:
User Account:
├─ Role: Supplier
├─ Supplier: (None) ← NOT LINKED!
└─ Problem: User can login but sees no orders!

✅ WITH Link:
User Account:
├─ Role: Supplier  
├─ Supplier: ABC Ingredients ← LINKED!
└─ Result: User sees all ABC Ingredients orders!
```

**The supplier field is what connects the user account to the supplier's orders!**

---

## 📋 Complete Example

### Example: Adding "ABC Ingredients Co."

#### Step 1: Create Supplier Record

```
Admin Panel → Suppliers → Add Supplier

Name: ABC Ingredients Co.
Contact Person: Juan Dela Cruz
Phone: +63 917 123 4567
Email: orders@abcingredients.com
Address: 123 Supply Street, Manila
☑ Is active

[Save]

✅ Supplier "ABC Ingredients Co." created
```

#### Step 2: Create Supplier User Account

```
Admin Panel → Users → Add User

Username: abc_supplier
Password: SecurePassword123!
Password confirmation: SecurePassword123!

First name: Juan
Last name: Dela Cruz
Email: orders@abcingredients.com

Role: Supplier ← IMPORTANT!
Supplier: ABC Ingredients Co. ← MUST LINK!
☑ Active

[Save]

✅ Supplier user "abc_supplier" created and linked!
```

#### Step 3: Give Login Info to Supplier

```
Email to ABC Ingredients:
─────────────────────────────
To: orders@abcingredients.com
Subject: Your Supplier Portal Access

Dear Juan,

Your supplier portal account has been created!

Login URL: https://yourdomain.com/supplier/login/
Username: abc_supplier
Password: SecurePassword123!

Please login and change your password on first use.

You can now:
- View purchase orders
- Approve orders with pricing
- Set delivery dates
- Mark orders as shipped
- View order history

Need help? Contact us at support@yoursystem.com

Best regards,
BIT Management Team
─────────────────────────────
```

---

## 🔍 How to Verify It's Working

### Test the Account

```
1. Go to: /supplier/login/

2. Enter credentials:
   Username: abc_supplier
   Password: SecurePassword123!

3. Click "Login to Supplier Portal"

4. Should see:
   ├─ Supplier Dashboard
   ├─ Company name: "ABC Ingredients Co."
   ├─ Statistics cards
   └─ If no orders yet: "No recent orders"

✅ If you see this, it's working correctly!
```

### Troubleshooting

**Problem**: Can login but see "No orders"
**Cause**: Likely working correctly - just no orders yet
**Solution**: Create a test purchase order

**Problem**: Can't login at all
**Cause**: Wrong credentials or account not active
**Solution**: 
- Verify username in admin panel
- Check "Active" is checked
- Reset password if needed

**Problem**: Can login but get permission error
**Cause**: Role is not set to "Supplier"
**Solution**: 
- Go to admin → Users → Find user
- Change Role to "Supplier"
- Save

**Problem**: Can login but no supplier name shown
**Cause**: Supplier link not set
**Solution**:
- Go to admin → Users → Find user
- Set "Supplier" field to link to supplier record
- Save

---

## 📊 Quick Reference

### Required Fields Summary

**For Supplier Record**:
- ✅ Name (required)
- ✅ Is active (check this!)
- Optional: Contact person, phone, email, address

**For Supplier User**:
- ✅ Username (required)
- ✅ Password (required)
- ✅ Email (required)
- ✅ Role = "Supplier" (required!)
- ✅ Supplier link (required!)
- ✅ Active (required!)

---

## 🎯 Multiple Suppliers

### Adding Multiple Suppliers

Repeat the process for each supplier:

```
Supplier 1: ABC Ingredients
├─ Step 1: Create supplier "ABC Ingredients"
├─ Step 2: Create user "abc_supplier"
└─ Link them together

Supplier 2: XYZ Supplies
├─ Step 1: Create supplier "XYZ Supplies"
├─ Step 2: Create user "xyz_supplier"
└─ Link them together

Supplier 3: Premium Foods
├─ Step 1: Create supplier "Premium Foods"
├─ Step 2: Create user "premium_supplier"
└─> Link them together

Each supplier user sees only THEIR orders!
```

---

## 🔐 Security Notes

### Account Security

- Use strong passwords
- Don't share accounts between suppliers
- Each supplier should have their own account
- Deactivate accounts if supplier relationship ends
- Regularly audit supplier access

### Data Isolation

```
Supplier User "ABC":
├─ Can see: ABC's orders only
├─ Cannot see: XYZ's orders
├─ Cannot see: Premium's orders
└─ Cannot access: Staff functions

This is automatic! ✅
```

---

## 🎓 Best Practices

### Naming Conventions

**Username Pattern**:
```
Good: abc_supplier, xyz_supplier, premium_supplier
Bad: user1, supplier, test
```

**Why**: Easy to identify and manage

### Email Addresses

**Use**:
- ✅ Supplier's official email
- ✅ Same email in both records
- ✅ Email that supplier checks regularly

**Don't Use**:
- ❌ Personal emails
- ❌ Temporary emails
- ❌ Unmonitored emails

### Contact Information

Always fill in:
- ✅ Phone number (for emergencies)
- ✅ Email (for notifications)
- ✅ Contact person (who to talk to)
- ✅ Address (for deliveries)

---

## 📝 Checklist

### Adding a New Supplier - Complete Checklist

```
Pre-Work:
[ ] Know supplier company name
[ ] Have contact person details
[ ] Have email and phone
[ ] Decide on username

Step 1: Supplier Record
[ ] Login to admin panel
[ ] Navigate to Suppliers
[ ] Click "Add Supplier"
[ ] Fill in name (required)
[ ] Fill in contact person
[ ] Fill in phone
[ ] Fill in email
[ ] Fill in address
[ ] Check "Is active"
[ ] Click Save
[ ] Verify supplier appears in list

Step 2: User Account
[ ] Still in admin panel
[ ] Navigate to Users
[ ] Click "Add User"
[ ] Enter username
[ ] Enter password (twice)
[ ] Enter first & last name
[ ] Enter email
[ ] Set Role to "Supplier" ← CRITICAL!
[ ] Select Supplier from dropdown ← CRITICAL!
[ ] Check "Active"
[ ] Click Save
[ ] Verify user appears in list

Step 3: Verification
[ ] Logout from admin
[ ] Go to /supplier/login/
[ ] Login with new credentials
[ ] See supplier dashboard
[ ] Verify supplier name shows
[ ] Check no errors

Step 4: Inform Supplier
[ ] Send login credentials securely
[ ] Provide login URL
[ ] Send quick start guide
[ ] Offer training/support

✅ Done!
```

---

## 🚀 Quick Start Commands

### For Admins

**To create supplier + account in one flow**:

```
1. Go to: /admin/

2. Create Supplier:
   Suppliers → Add → Fill form → Save
   
3. Create User (immediately after):
   Users → Add → Fill form:
   ├─ Username: {name}_supplier
   ├─ Password: (strong password)
   ├─ Role: Supplier ← MUST!
   ├─ Supplier: Select the one you just created ← MUST!
   └─ Save

4. Test:
   Open incognito window → /supplier/login/
   Login with new credentials
   Verify dashboard shows

5. Done!
   Send credentials to supplier
```

---

## 💡 Common Questions

**Q: Can one supplier have multiple user accounts?**  
A: Currently no - one user account per supplier. But you can have multiple contact persons in the notes.

**Q: Can we change the supplier later?**  
A: Yes, in admin panel, edit the user and change the supplier link.

**Q: What if supplier doesn't have email?**  
A: Email is required for the user account. Use their business contact email.

**Q: Can supplier change their password?**  
A: Currently through admin only. Password reset feature can be added later.

**Q: How do we deactivate a supplier?**  
A: Uncheck "Active" in both supplier record AND user account.

**Q: Can suppliers see each other's data?**  
A: No! Complete data isolation. Each supplier sees only their own orders.

---

## 🎯 Example Scenarios

### Scenario 1: Adding First Supplier

```
Your First Supplier: Manila Flour Mills

Step 1: Create Supplier
  Admin → Suppliers → Add
  ├─ Name: Manila Flour Mills
  ├─ Contact: Maria Santos
  ├─ Phone: +63 2 8123 4567
  ├─ Email: orders@manilaflour.com
  └─ Save

Step 2: Create Account
  Admin → Users → Add
  ├─ Username: manila_flour
  ├─ Password: (strong password)
  ├─ Role: Supplier
  ├─ Supplier: Manila Flour Mills
  └─ Save

Step 3: Test
  → /supplier/login/
  → Login as manila_flour
  ✅ Working!

Step 4: Inform Supplier
  Email Maria the login info
```

### Scenario 2: Multiple Suppliers

```
Supplier 1: ABC Ingredients
├─ Supplier record: "ABC Ingredients Co."
├─ User: abc_supplier
└─ Email: orders@abc.com

Supplier 2: Fresh Produce Inc.
├─ Supplier record: "Fresh Produce Inc."
├─ User: fresh_produce
└─ Email: orders@freshproduce.com

Supplier 3: Dairy Direct
├─ Supplier record: "Dairy Direct"
├─ User: dairy_direct
└─ Email: orders@dairydirect.com

Each has independent access!
```

### Scenario 3: Updating Supplier Info

```
Need to update phone number:

Step 1: Update Supplier Record
  Admin → Suppliers → Find supplier → Edit
  ├─ Update phone number
  └─ Save

Step 2: Update User (if needed)
  Admin → Users → Find supplier user → Edit
  ├─ Update email if changed
  └─ Save

✅ Changes reflected immediately!
```

---

## 🎨 Visual Guide

### Admin Panel Navigation

```
Admin Panel Home
│
├─> INVENTORY Section
│   │
│   ├─> Suppliers ← STEP 1: Click here first
│   │   │
│   │   ├─> Add Supplier [+]
│   │   │   ├─ Fill company info
│   │   │   └─ Save
│   │   │
│   │   └─> Supplier List
│   │       └─ Verify created
│   │
│   └─> (Other inventory models)
│
└─> AUTHENTICATION AND AUTHORIZATION
    │
    └─> Users ← STEP 2: Click here second
        │
        ├─> Add User [+]
        │   ├─ Fill user info
        │   ├─ Role: Supplier
        │   ├─ Supplier: Link to record
        │   └─ Save
        │
        └─> User List
            └─ Verify created
```

### Supplier Login Flow

```
Supplier receives email with:
├─ URL: /supplier/login/
├─ Username: abc_supplier
└─ Password: SecurePass123!

Supplier goes to URL:
└─> Enter credentials
    └─> Click "Login"
        └─> Redirects to dashboard
            └─> See company name & orders
                ✅ Success!
```

---

## 📋 Troubleshooting Guide

### Issue 1: Supplier field not showing in user form

**Cause**: Viewing wrong form or need to scroll
**Solution**:
- Look for "Supplier" field in the form
- It's in the main section, not in permissions
- Should be a dropdown showing all suppliers

### Issue 2: Can't find the supplier in dropdown

**Cause**: Supplier not created yet or not active
**Solution**:
- Go back to Step 1
- Create supplier record first
- Make sure "Is active" is checked
- Refresh user form

### Issue 3: Supplier can't see any orders

**Cause**: User not linked to supplier
**Solution**:
- Admin → Users → Find supplier user
- Check "Supplier" field is set
- Should show supplier name
- If blank, select supplier from dropdown
- Save

### Issue 4: "This is not a supplier account" error

**Cause**: Role not set to "Supplier"
**Solution**:
- Admin → Users → Find user
- Change "Role" to "Supplier"
- Make sure "Supplier" field is also set
- Save

---

## ✅ Verification Checklist

After creating supplier + account:

```
[ ] Supplier record exists in Suppliers list
[ ] Supplier is marked as Active
[ ] User account exists in Users list
[ ] User role is set to "Supplier"
[ ] User is linked to Supplier record (dropdown filled)
[ ] User is marked as Active
[ ] Can login at /supplier/login/
[ ] Dashboard shows supplier name
[ ] Can navigate to orders page
[ ] No permission errors

If all checked: ✅ Successfully created!
```

---

## 🎉 Success!

### You Now Know How To:

✅ Create supplier company records  
✅ Create supplier user accounts  
✅ Link users to suppliers  
✅ Set correct roles and permissions  
✅ Verify everything works  
✅ Troubleshoot common issues  

### Next Steps:

1. Create your suppliers
2. Create their accounts
3. Send them login info
4. Test with a purchase order
5. Start using the system!

---

## 📞 Need Help?

### Common Support Questions

**"I created the user but they can't see orders"**
→ Check the Supplier link field is set!

**"What's the difference between supplier record and user?"**
→ Supplier record = company info (like a Rolodex entry)
→ User account = login access (like giving them a key)
→ You need BOTH and they must be LINKED!

**"Can I create the user first?"**
→ No! Create supplier record first, then user.
→ You need the supplier to exist before you can link to it.

**"How many suppliers can I add?"**
→ Unlimited! Add as many as you need.

---

**Guide Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: ✅ Complete

🎊 **You're ready to add suppliers and their accounts!** 🎊

