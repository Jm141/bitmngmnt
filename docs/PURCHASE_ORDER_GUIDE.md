# Purchase Order Management System - Complete Guide

## Overview

The Purchase Order Management System is a comprehensive feature that allows you to manage the entire procurement workflow from ordering ingredients from suppliers to receiving deliveries with QR code scanning. This system includes:

- **Pre-order Creation**: Create purchase orders with multiple items
- **Supplier Workflow**: Supplier approval and order confirmation
- **QR Code Tracking**: Unique QR codes for each order
- **Automated Receiving**: Scan QR codes to automatically receive orders
- **Bulk Stock Management**: All items are automatically added to inventory when received
- **Order Tracking**: Complete timeline and status tracking

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Purchase Orders](#creating-purchase-orders)
3. [Order Workflow](#order-workflow)
4. [QR Code System](#qr-code-system)
5. [Receiving Orders](#receiving-orders)
6. [Order Status Management](#order-status-management)
7. [Integration with Inventory](#integration-with-inventory)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before using the Purchase Order system, ensure you have:

1. **Suppliers Set Up**: Add active suppliers in the system
2. **Items Configured**: Have items (especially ingredients) properly configured
3. **QR Code Support**: Install the qrcode library (already in requirements.txt)
4. **Permissions**: Users need `inventory_write` permission to manage orders

### Installation

The purchase order system is already integrated. To ensure all dependencies are installed:

```bash
pip install -r requirements.txt
python manage.py migrate
```

---

## Creating Purchase Orders

### Step-by-Step Process

1. **Navigate to Purchase Orders**
   - Go to: Inventory > Purchase Orders
   - Or use URL: `/purchase-orders/`

2. **Create New Order**
   - Click "Create Purchase Order" button
   - Fill in order information:
     - **Supplier**: Select the supplier (required)
     - **Expected Delivery Date**: When you expect the delivery (optional)
     - **Notes**: Any additional information

3. **Add Items to Order**
   - Click "Add Item" to add an order line
   - For each item:
     - Select the Item from dropdown
     - Enter Quantity
     - Enter Unit Price
     - Add item-specific notes (optional)
   - You can add multiple items to a single order

4. **Review and Submit**
   - Check total items and total amount
   - Click "Create Purchase Order"
   - Order will be created with status "Pending"

### Example Order Creation

```python
# Example data for creating an order
Supplier: ABC Ingredients Co.
Expected Delivery: 2025-11-01
Items:
  - Flour (25kg bags) x 10 @ ₱800.00 = ₱8,000.00
  - Sugar (50kg bags) x 5 @ ₱1,200.00 = ₱6,000.00
  - Salt (1kg packs) x 20 @ ₱50.00 = ₱1,000.00
Total Amount: ₱15,000.00
```

---

## Order Workflow

The purchase order follows a specific workflow with multiple states:

### Order States

1. **Draft** - Order is being created (not used in current implementation)
2. **Pending** - Order has been submitted, waiting for supplier approval
3. **Approved** - Supplier has confirmed the order
4. **Shipped** - Order has been dispatched by supplier
5. **Received** - Order has been delivered and accepted
6. **Cancelled** - Order was cancelled

### Workflow Diagram

```
┌──────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│ Pending  │ --> │ Approved │ --> │ Shipped │ --> │ Received │
└──────────┘     └──────────┘     └─────────┘     └──────────┘
     │                                                    
     └──────────────> Cancelled
```

### State Transitions

**Pending → Approved**
- Action: Supplier approves order
- URL: `/purchase-orders/<id>/approve/`
- Requirements: Order must be in "Pending" status
- Result: Order status changes to "Approved", expected delivery date is set

**Approved → Shipped**
- Action: Mark order as shipped
- URL: `/purchase-orders/<id>/ship/`
- Requirements: Order must be in "Approved" status
- Result: Order status changes to "Shipped", shipped_at timestamp is recorded

**Shipped → Received**
- Action: Scan QR code to receive order
- URL: `/purchase-orders/scan/receive/`
- Requirements: Order must be in "Shipped" status
- Result: 
  - Order status changes to "Received"
  - All items automatically added to inventory as stock lots
  - Stock quantities updated

---

## QR Code System

### QR Code Generation

Each purchase order automatically generates a unique QR code when created:

- **Format**: `PO-{16-character hash}`
- **Example**: `PO-A3F7D9E2B1C4A6F8`
- **Algorithm**: SHA-256 hash of order details + timestamp
- **Uniqueness**: Guaranteed unique for each order

### QR Code Usage

1. **Viewing QR Code**
   - Open purchase order detail page
   - QR code is displayed on the right sidebar
   - Code can be printed for physical attachment to shipment

2. **QR Code Image**
   - Generated as base64-encoded PNG
   - 250x250 pixels
   - High contrast black and white
   - Includes error correction

3. **Printing QR Code**
   - Click "Print QR Code" button
   - Print-friendly format automatically applied
   - Attach to shipping documents

### QR Code Format

```python
# QR Code contains the order's unique code string
qr_data = "PO-A3F7D9E2B1C4A6F8"

# When scanned, this code is used to:
# 1. Identify the specific purchase order
# 2. Validate the order is ready to be received
# 3. Trigger automated stock receiving
```

---

## Receiving Orders

### QR Scanning Process

1. **Navigate to Receive Page**
   - Go to: Purchase Orders > Scan & Receive
   - Or URL: `/purchase-orders/scan/receive/`

2. **Scan QR Code**
   - Place cursor in QR Code input field (auto-focused)
   - Scan the QR code from delivery package
   - Or manually enter the QR code
   - Press Enter or click "Receive Purchase Order"

3. **Automatic Processing**
   When you scan a valid QR code:
   
   a. **Order Validation**
      - System validates QR code exists
      - Checks order status is "Shipped"
      - Verifies order can be received
   
   b. **Status Update**
      - Order status → "Received"
      - received_at → current timestamp
      - received_by → current user
      - actual_delivery_date → today's date
   
   c. **Stock Lot Creation**
      For each item in the order:
      - Creates new StockLot
      - lot_no = `{order_no}-{item_code}`
      - qty = ordered quantity
      - unit_cost = order item unit price
      - supplier = order supplier
      - expires_at = calculated if perishable
   
   d. **Stock Movement Recording**
      - Creates StockMovement entry
      - movement_type = "receive"
      - Reference = order number
      - Notes = "Received from PO: {order_no}"
   
   e. **Order Items Update**
      - qty_received = qty_ordered
      - All items marked as fully received

4. **Success Confirmation**
   - Success message displayed
   - Shows number of items added
   - Redirects to order detail page

### Manual Receiving (Alternative)

If QR scanning is not available:

1. Go to order detail page
2. Note the QR code text (e.g., `PO-A3F7D9E2B1C4A6F8`)
3. Go to Scan & Receive page
4. Manually type the QR code
5. Submit the form

---

## Order Status Management

### Viewing All Orders

Navigate to Purchase Orders list page:
- URL: `/purchase-orders/`
- Shows all orders with filtering options
- Summary cards show counts by status

### Filtering Orders

Available filters:
- **Status**: All, Pending, Approved, Shipped, Received, Cancelled
- **Supplier**: Filter by specific supplier
- Filters can be combined

### Order Detail View

Each order detail page shows:

**Left Column:**
- Order information (number, supplier, status, dates)
- Complete item list with quantities and prices
- Supplier notes
- Internal notes
- Timeline of status changes

**Right Column:**
- QR code image
- QR code text
- Available actions (based on current status)
- Order timeline

### Available Actions

**For Pending Orders:**
- Approve Order → Mark as approved
- Cancel Order → Cancel the order

**For Approved Orders:**
- Mark as Shipped → Change status to shipped
- Cancel Order → Cancel the order

**For Shipped Orders:**
- Scan to Receive → Go to QR scanning page
- (Auto-receive functionality)

**For Received/Cancelled Orders:**
- View only (no actions available)

---

## Integration with Inventory

### Automatic Inventory Updates

When an order is received:

1. **Stock Lots Created**
   ```python
   # Each order item creates a stock lot
   StockLot(
       item=item,
       lot_no=f"{order_no}-{item_code}",  # e.g., "PO-20251017-0001-FLR001"
       qty=ordered_quantity,
       unit=item.unit,
       expires_at=calculated_expiry,
       unit_cost=unit_price,
       supplier=order.supplier,
       notes=f"Received from PO: {order_no}"
   )
   ```

2. **Expiry Date Calculation**
   - For perishable items: `today + shelf_life_days`
   - For non-perishable: No expiry date
   - Automatically follows item configuration

3. **Stock Movements**
   - Each stock lot creation records a movement
   - Type: "receive"
   - Tracks complete audit trail
   - Links to purchase order via ref_no

4. **Item Current Stock**
   - Item total stock automatically updated
   - Available immediately for consumption
   - Visible in inventory dashboard

### Viewing Received Items

After receiving an order:

1. **Order Detail Page**
   - Shows qty_received for each item
   - Status badges indicate fully received items

2. **Item Detail Page**
   - New stock lots appear in item's stock lot list
   - Shows reference to purchase order
   - Displays expiry dates

3. **Stock Movements**
   - Receive movements visible in item movements
   - Shows which PO the stock came from

---

## API Reference

### Models

#### PurchaseOrder

**Fields:**
- `id` (UUID): Primary key
- `order_no` (str): Auto-generated order number (PO-YYYYMMDD-XXXX)
- `supplier` (FK): Link to Supplier
- `status` (str): Order status (choices: draft, pending, approved, shipped, received, cancelled)
- `qr_code` (str): Unique QR code for tracking
- `order_date` (datetime): When order was created
- `expected_delivery_date` (date): Expected delivery
- `actual_delivery_date` (date): Actual delivery date
- `supplier_notes` (text): Notes from supplier
- `approved_at` (datetime): When approved
- `shipped_at` (datetime): When shipped
- `received_at` (datetime): When received
- `notes` (text): Internal notes
- `total_amount` (decimal): Total order value
- `created_by` (FK): User who created order
- `received_by` (FK): User who received order

**Methods:**
- `generate_order_no()`: Static method to generate order numbers
- `generate_qr_code()`: Generate unique QR code
- `calculate_total()`: Calculate total order amount
- `can_be_approved()`: Check if order can be approved
- `can_be_shipped()`: Check if order can be shipped
- `can_be_received()`: Check if order can be received
- `approve_order(supplier_notes, expected_delivery_date)`: Approve the order
- `mark_shipped()`: Mark order as shipped
- `mark_received(user)`: Mark order as received

#### PurchaseOrderItem

**Fields:**
- `id` (UUID): Primary key
- `purchase_order` (FK): Link to PurchaseOrder
- `item` (FK): Link to Item
- `qty_ordered` (decimal): Quantity ordered
- `unit` (str): Unit of measurement
- `unit_price` (decimal): Price per unit
- `qty_received` (decimal): Quantity received
- `notes` (text): Item-specific notes

**Methods:**
- `subtotal()`: Calculate line item total
- `is_fully_received()`: Check if fully received
- `remaining_qty()`: Calculate remaining quantity

### Services

#### PurchaseOrderService

**Methods:**

1. `create_purchase_order(supplier, items_data, user, notes, expected_delivery_date)`
   - Creates new purchase order with items
   - Returns: PurchaseOrder instance
   
2. `approve_purchase_order(po, supplier_notes, expected_delivery_date)`
   - Approves a purchase order
   - Returns: PurchaseOrder instance
   
3. `ship_purchase_order(po)`
   - Marks order as shipped
   - Returns: PurchaseOrder instance
   
4. `receive_purchase_order_by_qr(qr_code, user)`
   - Receives order by QR code
   - Returns: (PurchaseOrder, list of StockLots)
   
5. `generate_qr_code_image(qr_code)`
   - Generates base64 QR code image
   - Returns: base64 encoded image string
   
6. `get_pending_orders()`
   - Get all pending orders
   - Returns: QuerySet
   
7. `get_shipped_orders()`
   - Get all shipped orders
   - Returns: QuerySet
   
8. `get_order_summary()`
   - Get order statistics
   - Returns: dict with counts by status

### Views

**URLs:**
- `/purchase-orders/` - List all orders
- `/purchase-orders/create/` - Create new order
- `/purchase-orders/<id>/` - View order details
- `/purchase-orders/<id>/approve/` - Approve order
- `/purchase-orders/<id>/ship/` - Mark as shipped
- `/purchase-orders/<id>/cancel/` - Cancel order
- `/purchase-orders/scan/receive/` - QR scan page

**Permissions:**
- List/Detail: `inventory_read`
- Create/Edit/Actions: `inventory_write`

---

## Troubleshooting

### Common Issues

#### 1. QR Code Not Scanning

**Problem**: QR scanner doesn't recognize the code

**Solutions:**
- Ensure QR code is printed clearly
- Check scanner is configured for alphanumeric codes
- Try manual entry of QR code
- Verify QR code format starts with "PO-"

#### 2. Cannot Receive Order

**Problem**: Error when trying to receive order

**Possible Causes:**
- Order is not in "Shipped" status
  - Solution: Verify order status, mark as shipped first
- Invalid QR code
  - Solution: Check QR code matches an existing order
- Already received
  - Solution: Check order detail, may already be received

#### 3. Items Not Added to Inventory

**Problem**: After receiving, items don't appear in inventory

**Solutions:**
- Check order detail page to verify status is "Received"
- Navigate to each item detail page to see new stock lots
- Verify stock movements were created
- Check for any error messages in logs

#### 4. Incorrect Total Amount

**Problem**: Order total doesn't match expected

**Solutions:**
- Verify unit prices for each item
- Check quantities entered correctly
- Total is calculated automatically: sum(qty × unit_price)
- Refresh page to see updated total

### Error Messages

**"Invalid QR code. Purchase order not found."**
- The scanned QR code doesn't match any order in system
- Verify QR code is correct
- Check if order exists in system

**"Purchase order cannot be received. Current status: {status}"**
- Order is not in "Shipped" status
- Check order detail to see current status
- Follow workflow: Pending → Approved → Shipped → Received

**"Order cannot be approved in current status"**
- Order is not in "Pending" status
- Cannot re-approve already approved orders
- Check order status first

**"Please add at least one item to the purchase order."**
- Trying to create order without items
- Add at least one item before submitting

### Best Practices

1. **Creating Orders**
   - Always double-check quantities and prices
   - Include expected delivery date
   - Add notes for special instructions

2. **Approval Process**
   - Review order completely before approving
   - Set realistic delivery dates
   - Add supplier notes if there are changes

3. **Receiving Orders**
   - Always use QR code scanning for accuracy
   - Verify items match what was ordered
   - Check quality before accepting
   - Keep QR codes with delivery documents

4. **Inventory Management**
   - Monitor received items in inventory
   - Check expiry dates for perishables
   - Follow up on pending orders regularly

---

## Feature Highlights

### Automation Benefits

1. **Auto-Generated Order Numbers**
   - Format: PO-YYYYMMDD-XXXX
   - Sequential per day
   - Easy to track and reference

2. **Unique QR Codes**
   - Cryptographically secure
   - Prevents duplicate receiving
   - Fast order identification

3. **Bulk Stock Receiving**
   - All items processed at once
   - Automatic lot number generation
   - Instant inventory updates

4. **Expiry Date Calculation**
   - Based on item shelf life
   - Only for perishable items
   - Helps prevent waste

5. **Complete Audit Trail**
   - Every action logged
   - Timestamps recorded
   - User tracking
   - Full traceability

### Integration Points

- **Supplier Management**: Links to existing suppliers
- **Item Master**: Uses configured items
- **Stock Management**: Creates stock lots automatically
- **Inventory Service**: Uses FEFO/FIFO logic
- **User Permissions**: Respects access controls
- **Audit Logging**: All actions logged

---

## Future Enhancements

Potential improvements for the purchase order system:

1. **Email Notifications**
   - Notify supplier when order is created
   - Alert when order is approved
   - Remind about shipment dates

2. **Partial Receiving**
   - Allow receiving orders in multiple deliveries
   - Track partial fulfillment

3. **Mobile QR Scanner**
   - Dedicated mobile app
   - Camera-based scanning
   - Offline capability

4. **Supplier Portal**
   - Dedicated login for suppliers
   - Self-service approval
   - Shipment tracking

5. **Order Analytics**
   - Delivery time analysis
   - Supplier performance metrics
   - Cost trends

6. **Auto-Reordering**
   - Automatic PO creation for low stock
   - Based on reorder levels
   - Suggested order quantities

---

## Support

For issues or questions about the Purchase Order system:

1. Check this documentation
2. Review audit logs for error details
3. Contact system administrator
4. Check Django admin for detailed records

---

## Changelog

**Version 1.0** (October 2025)
- Initial release
- Core purchase order workflow
- QR code generation and scanning
- Automatic stock receiving
- Complete order tracking
- Supplier workflow support

---

**Document Version**: 1.0  
**Last Updated**: October 17, 2025  
**Author**: BIT Management System Development Team

