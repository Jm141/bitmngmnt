# 📋 Quick Reference Card

## For Daily Use - Keep This Handy!

---

## 🔑 Logins

| User Type | Login URL | Example Username |
|-----------|-----------|------------------|
| Staff/Admin | `/login/` | admin, staff_user |
| Supplier | `/supplier/login/` | abc_supplier, xyz_supplier |

---

## 🛒 Purchase Orders - For Admin

### How to See Purchase Orders

```
1. Login as Admin (/login/)
2. Look at left sidebar
3. Click "Purchase Orders" 🛒
4. See all orders!
```

### Quick Actions

| Action | Where to Click |
|--------|---------------|
| Create new order | [Create Purchase Order] button |
| Scan & receive | [Scan & Receive] button |
| View order | Click order number |
| Filter orders | Use dropdowns at top |

---

## 👥 Adding Suppliers - Two Steps!

### STEP 1: Create Supplier (Company)

```
Admin Panel → INVENTORY → Suppliers → Add Supplier

Fill:
├─ Name: ABC Ingredients Co. *
├─ Contact: Juan Dela Cruz
├─ Phone: +63 917 123 4567
├─ Email: orders@abc.com
├─ Address: 123 Supply St, Manila
└─ ☑ Is active

[Save] → ✅ Done!
```

### STEP 2: Create User Account (Login)

```
Admin Panel → AUTHENTICATION... → Users → Add User

PAGE 1:
├─ Username: abc_supplier *
├─ Password: SecurePass123! *
└─ Password (again): SecurePass123! *
[Save]

PAGE 2:
├─ First name: Juan
├─ Last name: Dela Cruz
├─ Email: orders@abc.com *
├─ Role: Supplier * ← MUST SELECT!
├─ Supplier: ABC Ingredients ← MUST LINK!
└─ ☑ Active ← MUST CHECK!
[Save] → ✅ Done!

Give to Supplier:
├─ URL: /supplier/login/
├─ Username: abc_supplier
└─ Password: SecurePass123!
```

---

## 🔄 Complete Workflow

### From Request to Receive

```
1. STAFF: Create Request
   ├─ Select supplier
   ├─ Add items + quantities
   ├─ NO prices needed!
   └─> Status: PENDING

2. SUPPLIER: Approve with Pricing
   ├─ Login to portal
   ├─ Enter price for each item
   ├─ Set delivery date
   └─> Status: APPROVED

3. SUPPLIER: Ship
   ├─ Print QR code
   ├─ Attach to package
   └─> Status: SHIPPED

4. STAFF: Receive
   ├─ Scan QR code
   └─> Status: RECEIVED
       └─> Inventory auto-updated!
```

---

## ⚠️ Critical Checklist

When creating supplier accounts:

```
✅ Create supplier record FIRST
✅ Create user account SECOND
✅ Set role to "Supplier"
✅ Link user to supplier
✅ Both marked as "Active"
✅ Test login before giving to supplier
```

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Don't see Purchase Orders | Refresh browser (Ctrl+F5) |
| Supplier dropdown empty | Create supplier record first |
| Supplier sees no orders | Check user is linked to supplier |
| Can't login | Check "Active" is checked |
| Permission error | Verify role = "Supplier" |

---

## 📱 URLs At a Glance

```
Admin Panel:        /admin/
Staff Login:        /login/
Supplier Login:     /supplier/login/
Purchase Orders:    /purchase-orders/
Create Order:       /purchase-orders/create/
Scan & Receive:     /purchase-orders/scan/receive/
Supplier Dashboard: /supplier/dashboard/
```

---

## 💡 Pro Tips

1. **Username Format**: Use `{company}_supplier` (easy to remember)
2. **Test First**: Always test login before giving to supplier
3. **Document**: Keep list of supplier usernames
4. **Security**: Change default passwords
5. **Refresh**: Ctrl+F5 if menu doesn't show

---

## 🎯 Quick Test

### Test the System (5 minutes)

```
1. Create test supplier "Test Co."
2. Create user "test_supplier"
3. Link them together
4. Test login at /supplier/login/
5. Create test purchase order
6. Supplier approves with pricing
7. Mark as shipped
8. Scan QR to receive
✅ If all works = System ready!
```

---

## 📞 Need Help?

**Read Full Guides:**
- HOW_TO_ADD_SUPPLIER_ACCOUNTS.md (detailed)
- VISUAL_SETUP_GUIDE.md (with diagrams)
- ADMIN_QUESTIONS_ANSWERED.md (Q&A)

**Still Stuck?**
- Check audit logs for errors
- Verify all steps completed
- Review user permissions

---

**Quick Ref Version**: 1.0  
**Print this page for your desk!** 🖨️

🎊 **Everything you need in one page!** 🎊

