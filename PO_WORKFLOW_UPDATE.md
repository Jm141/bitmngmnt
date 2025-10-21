# Purchase Order Workflow - Updated

## ✅ New Workflow Implemented

The Purchase Order process now includes **Admin Approval** after Supplier Approval, with cancellation reasons required!

---

## 🔄 **New Workflow Steps**

### **1. Draft → Pending**
- Staff creates purchase order
- Adds items and quantities
- Submits to supplier

### **2. Pending → Supplier Approved**
- Supplier reviews order
- Supplier adds pricing for each item
- Supplier sets expected delivery date
- Supplier approves order
- **Status**: "Approved by Supplier - Pending Admin Review"

### **3. Supplier Approved → Admin Approved** ⭐ NEW!
- Admin reviews supplier pricing
- **Admin can:**
  - ✅ **Approve**: If price is acceptable → Status: "Approved by Admin - Ready to Ship"
  - ❌ **Reject**: If price is too high → Returns to "Pending" status
    - Must provide rejection reason
    - Supplier can re-submit with new pricing

### **4. Admin Approved → Shipped**
- Supplier marks order as shipped
- Only possible after admin approval

### **5. Shipped → Received**
- Staff scans QR code
- System creates stock lots
- Order complete

---

## 🚫 **Cancellation Process** ⭐ NEW!

Both **Supplier** and **Admin** can cancel orders at any stage (except Received):

### **Who Can Cancel:**
- **Supplier**: Can cancel if they cannot fulfill the order
- **Admin**: Can cancel if order is no longer needed

### **Cancellation Requirements:**
- **Must provide reason** (required field)
- Examples:
  - "Items out of stock"
  - "Price increased significantly"
  - "Order no longer needed"
  - "Supplier cannot meet delivery date"

### **Cancellation Tracking:**
- Cancelled by (user)
- Cancelled at (timestamp)
- Cancellation reason (text)

---

## 📊 **Status Flow Diagram**

```
Draft
  ↓
Pending Supplier Approval
  ↓
Approved by Supplier ──→ [Admin Reviews]
  ↓                           ↓
  ↓                      [Reject] → Back to Pending
  ↓                           ↓
  ↓                      [Approve]
  ↓                           ↓
Admin Approved - Ready to Ship
  ↓
Shipped
  ↓
Received
```

**Cancellation** can happen at any point before "Received"

---

## 🎯 **Key Features**

### **1. Supplier Approval**
- Supplier adds unit prices
- Sets expected delivery date
- Adds supplier notes
- Status changes to "Supplier Approved"

### **2. Admin Approval** ⭐ NEW!
- Admin reviews total order cost
- Can approve if price is acceptable
- Can reject if price is too high
- Rejection sends order back to "Pending"
- Supplier must re-approve with new pricing

### **3. Admin Rejection** ⭐ NEW!
- **Reason required**
- Examples:
  - "Price exceeds budget"
  - "Price 20% higher than expected"
  - "Found better supplier"
- Order returns to "Pending" status
- Supplier can see rejection reason
- Supplier can cancel or re-submit

### **4. Cancellation with Reason** ⭐ NEW!
- Both parties can cancel
- **Reason is mandatory**
- Tracked in database:
  - `cancelled_at`
  - `cancelled_by`
  - `cancellation_reason`

---

## 💾 **Database Changes**

### **New Fields Added:**

```python
# Supplier approval tracking
supplier_approved_at = DateTimeField
supplier_approved_by = ForeignKey(User)

# Admin approval tracking
admin_notes = TextField
admin_approved_at = DateTimeField
admin_approved_by = ForeignKey(User)

# Cancellation tracking
cancelled_at = DateTimeField
cancelled_by = ForeignKey(User)
cancellation_reason = TextField
```

### **Updated Status Choices:**

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending Supplier Approval'),
    ('supplier_approved', 'Approved by Supplier - Pending Admin Review'),
    ('admin_approved', 'Approved by Admin - Ready to Ship'),
    ('shipped', 'Shipped'),
    ('received', 'Received'),
    ('cancelled', 'Cancelled'),
]
```

---

## 🔧 **New Views & URLs**

### **Admin Approval View**
- **URL**: `/purchase-orders/<order_id>/admin-approve/`
- **Method**: POST
- **Permission**: Admin required
- **Action**: Approves order after supplier pricing

### **Admin Rejection View**
- **URL**: `/purchase-orders/<order_id>/admin-reject/`
- **Method**: POST
- **Permission**: Admin required
- **Requires**: Rejection reason
- **Action**: Sends order back to pending

### **Updated Cancel View**
- **URL**: `/purchase-orders/<order_id>/cancel/`
- **Method**: POST
- **Requires**: Cancellation reason
- **Action**: Cancels order with reason

---

## 📝 **Usage Examples**

### **Scenario 1: Normal Flow**
1. Staff creates PO for 100kg flour
2. Supplier approves with ₱50/kg = ₱5,000 total
3. Admin reviews: ✅ Approved (within budget)
4. Supplier ships
5. Staff receives

### **Scenario 2: Price Too High**
1. Staff creates PO for 100kg sugar
2. Supplier approves with ₱100/kg = ₱10,000 total
3. Admin reviews: ❌ Rejected
   - Reason: "Price exceeds budget by 50%"
4. Order returns to "Pending"
5. Supplier can:
   - Re-approve with lower price
   - Cancel with reason "Cannot meet price requirement"

### **Scenario 3: Supplier Cancellation**
1. Staff creates PO for 50kg coffee beans
2. Supplier reviews order
3. Supplier cancels:
   - Reason: "Coffee beans out of stock until next month"
4. Staff creates new PO with different supplier

### **Scenario 4: Admin Cancellation**
1. Staff creates PO for 200 boxes
2. Supplier approves with pricing
3. Admin cancels:
   - Reason: "Project cancelled, items no longer needed"

---

## 🎨 **UI Changes Needed**

### **Purchase Order Detail Page:**
- Show supplier approval info (date, user, notes)
- Show admin approval info (date, user, notes)
- Show cancellation info (date, user, reason)
- **Buttons based on status:**
  - If "Supplier Approved": Show "Admin Approve" and "Admin Reject" buttons
  - If "Admin Approved": Show "Ship" button
  - If not "Received" or "Cancelled": Show "Cancel" button

### **New Templates to Create:**
1. `purchase_order_admin_approve.html` - Admin approval form
2. `purchase_order_admin_reject.html` - Admin rejection form with reason
3. `purchase_order_cancel.html` - Cancellation form with reason

---

## ✅ **Migration Applied**

Migration `0009_rename_approved_at_purchaseorder_admin_approved_at_and_more.py` has been created and applied.

**Changes:**
- Renamed `approved_at` → `admin_approved_at`
- Added `admin_approved_by`
- Added `admin_notes`
- Added `supplier_approved_at`
- Added `supplier_approved_by`
- Added `cancelled_at`
- Added `cancelled_by`
- Added `cancellation_reason`
- Updated status field max_length to 30

---

## 🔐 **Permissions**

- **Create PO**: Staff with inventory_write permission
- **Supplier Approve**: Supplier users only
- **Admin Approve/Reject**: Admin or Super Admin only
- **Ship**: Supplier users only
- **Receive**: Staff with inventory_write permission
- **Cancel**: Admin/Super Admin or Supplier (with reason)

---

## 📊 **Benefits**

1. **Cost Control**: Admin can reject overpriced orders
2. **Transparency**: All approvals and rejections are tracked
3. **Accountability**: Reasons required for rejections and cancellations
4. **Flexibility**: Both parties can cancel with valid reasons
5. **Audit Trail**: Complete history of who did what and when
6. **Better Communication**: Rejection reasons help suppliers understand issues

---

**Status**: ✅ **IMPLEMENTED**  
**Date**: October 21, 2025  
**Files Modified**:
- `inventory/models.py` - Updated PurchaseOrder model
- `inventory/admin.py` - Updated admin fieldsets
- `inventory/services.py` - Added new service methods
- `inventory/views.py` - Added admin approve/reject/cancel views
- `inventory/urls.py` - Added new URL patterns
- Migration created and applied

**Next Steps**:
- Create HTML templates for admin approve, reject, and cancel forms
- Update purchase order detail page to show new buttons
- Test the complete workflow
