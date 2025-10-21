# Purchase Order - Low Stock Items Feature

## ✅ Feature Implemented

The Purchase Order creation page now displays all **low stock items** with checkboxes for easy selection!

---

## 🎯 What Was Changed

### **1. Backend Changes** (`inventory/views.py`)
- Modified `purchase_order_create` function to identify and pass low stock items to the template
- Calculates current stock for each item
- Compares against reorder level
- Includes suggested order quantity (minimum order quantity)
- Flags out-of-stock items

### **2. Frontend Changes** (`purchase_order_form.html`)
- Added **Low Stock Items** section at the top of the form
- Displays items in a table with:
  - Checkbox for selection
  - Item Code
  - Item Name
  - Current Stock (with color-coded badges)
  - Reorder Level
  - Suggested Quantity
  - Unit
  - Status (Out of Stock / Low Stock)

---

## 📋 How to Use

### **Step 1: Navigate to Create Purchase Order**
- Go to **Purchase Orders** → **Create Purchase Order**

### **Step 2: View Low Stock Items**
- At the top of the page, you'll see a **yellow warning card** showing all low stock items
- **Red rows** = Out of Stock (0 quantity)
- **Yellow rows** = Low Stock (below reorder level)

### **Step 3: Select Items to Order**
You have 3 options:

**Option A: Select Individual Items**
- Check the boxes next to items you want to order

**Option B: Select All**
- Click **"Select All"** button to check all low stock items

**Option C: Use the "Select All" Checkbox**
- Check the checkbox in the table header to select all items

### **Step 4: Add to Order**
- Click **"Add Selected Items to Order"** button
- Selected items will be automatically added to the Order Items section
- Quantities are pre-filled with the **minimum order quantity**
- You can adjust quantities as needed

### **Step 5: Complete the Order**
- Select supplier
- Review and adjust quantities
- Add notes if needed
- Click **"Create Purchase Order"**

---

## 🎨 Visual Features

### **Color Coding**
- 🔴 **Red Badge** = Out of Stock (0 items)
- 🟡 **Yellow Badge** = Low Stock (below reorder level)
- 🟢 **Green Border** = Items added to order

### **Smart Features**
- ✅ Prevents duplicate items (won't add if already in order)
- ✅ Pre-fills suggested quantities
- ✅ Shows current stock vs reorder level
- ✅ Clear selection after adding
- ✅ Success confirmation message

---

## 📊 Example Scenario

**Before:**
- You had to manually search and add each low stock item one by one
- No visibility into which items need reordering
- Risk of forgetting critical items

**After:**
1. Open Create Purchase Order page
2. See **"Low Stock Items (5 items)"** warning card
3. Review the list:
   - Flour: 2 kg (Reorder: 10 kg) - **Low Stock**
   - Sugar: 0 kg (Reorder: 5 kg) - **Out of Stock**
   - Salt: 1 kg (Reorder: 3 kg) - **Low Stock**
4. Click "Select All"
5. Click "Add Selected Items to Order"
6. All 5 items added with suggested quantities
7. Adjust quantities if needed
8. Submit order

**Time saved:** ~5 minutes per order!

---

## 🔧 Technical Details

### **Low Stock Detection Logic**
```python
current_stock <= reorder_level
```

### **Suggested Quantity**
- Uses the `min_order_qty` field from the Item model
- Can be manually adjusted after adding to order

### **Data Passed to Template**
```python
{
    'item': Item object,
    'current_stock': Decimal,
    'reorder_level': Decimal,
    'min_order_qty': Decimal,
    'is_out_of_stock': Boolean
}
```

---

## 💡 Benefits

1. **Faster Order Creation** - Select multiple items at once
2. **Better Visibility** - See all low stock items in one place
3. **Prevent Stock-Outs** - Never miss critical items
4. **Smart Suggestions** - Pre-filled quantities based on min order qty
5. **Error Prevention** - Can't add duplicate items
6. **Color-Coded Alerts** - Instantly identify critical items

---

## 🚀 Future Enhancements (Optional)

- Add "Quick Order All Low Stock" button
- Email notifications for low stock items
- Export low stock list to Excel
- Filter by category or supplier
- Show last order date for each item
- Suggest supplier based on previous orders

---

## 📝 Notes

- The low stock section only appears if there are items below reorder level
- You can still manually add items using the "Add Item" button
- Items can be added from both the low stock section AND manually
- The system prevents adding the same item twice

---

**Feature Status:** ✅ **COMPLETED**  
**Date Implemented:** October 21, 2025  
**Files Modified:** 
- `inventory/views.py`
- `inventory/templates/inventory/purchase_order_form.html`
