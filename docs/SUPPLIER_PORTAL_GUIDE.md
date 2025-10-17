# Supplier Portal - Complete Guide

## 🎉 Overview

The Supplier Portal is a dedicated interface that allows suppliers to have their own accounts and manage purchase orders independently. This feature improves communication, data accuracy, and streamlines the ordering workflow.

## ✨ Key Features

- **Dedicated Supplier Accounts**: Each supplier can have their own login
- **Separate Login Portal**: Suppliers use a dedicated login page
- **Order Management**: View all orders sent to them
- **Approve Orders**: Suppliers can approve/reject orders
- **Ship Orders**: Mark orders as shipped when ready
- **QR Code Access**: Print QR codes for shipments
- **Order History**: View complete order history and statistics
- **Dashboard**: Overview of all order statuses

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Supplier Accounts](#creating-supplier-accounts)
3. [Supplier Login](#supplier-login)
4. [Supplier Dashboard](#supplier-dashboard)
5. [Managing Orders](#managing-orders)
6. [Order Workflow](#order-workflow)
7. [Technical Details](#technical-details)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

1. **Migrations Applied**: Ensure all migrations are run
   ```bash
   python manage.py migrate
   ```

2. **Supplier Records**: Have suppliers created in the system
3. **Admin Access**: Need admin account to create supplier users

### Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│  Staff      │────────>│  Purchase Order  │<────────│  Supplier    │
│  (Creates)  │         │   (Pending)      │         │  (Approves)  │
└─────────────┘         └──────────────────┘         └──────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Order Approved  │
                        └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Supplier Ships  │────> QR Code Generated
                        └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Staff Receives  │────> Scan QR Code
                        └──────────────────┘────> Auto-add to Inventory
```

---

## Creating Supplier Accounts

### Method 1: Via Django Admin

1. **Login to Django Admin**
   - URL: `/admin/`
   - Use admin credentials

2. **Navigate to Users**
   - Click "Users" in the admin panel

3. **Add New User**
   - Click "Add User" button
   - Fill in required information:
     - **Username**: e.g., `abc_supplier`
     - **Password**: Set a strong password
     - **Role**: Select "Supplier"
     - **First Name**: Supplier contact person name
     - **Email**: Supplier email address
     - **Supplier**: Link to the supplier record (important!)

4. **Save**
   - Click "Save" to create the account

### Method 2: Via Management Command (Future)

```python
# management/commands/create_supplier_user.py
python manage.py create_supplier_user --supplier "ABC Ingredients" --username "abc_supplier" --email "orders@abcingredients.com"
```

### Important Notes

- **One Account Per Supplier**: Each supplier should have one user account
- **Link to Supplier Record**: Must link the user to an existing Supplier record
- **Role Must Be "Supplier"**: Ensure role is set to "supplier"
- **Email Required**: Supplier email is required for future notifications

---

## Supplier Login

### Login URL

Suppliers use a dedicated login page:
```
/supplier/login/
```

### Login Process

1. **Navigate to Supplier Portal**
   - Go to: `yourdomain.com/supplier/login/`
   - Or click "Supplier Portal" link from main site

2. **Enter Credentials**
   - Username: Provided by admin
   - Password: Set during account creation

3. **Access Dashboard**
   - Successfully logged in users are redirected to supplier dashboard
   - Regular staff cannot access supplier portal
   - Suppliers cannot access staff dashboard

### Security Features

- **Role-Based Access**: Only supplier accounts can access
- **Separate Session**: Independent from staff sessions
- **Audit Logging**: All supplier actions are logged
- **Secure Authentication**: Standard Django authentication

---

## Supplier Dashboard

### Dashboard URL
```
/supplier/dashboard/
```

### Dashboard Components

#### 1. **Statistics Cards**
- **Pending Orders**: Orders waiting for approval
- **Approved Orders**: Orders ready to ship
- **Shipped Orders**: Orders currently in transit
- **Received Orders**: Completed orders

#### 2. **Total Order Value**
- Shows cumulative value of all orders
- Includes approved, shipped, and received orders
- Displayed prominently at top

#### 3. **Recent Orders Table**
- Last 5 most recent orders
- Quick status view
- Direct links to order details

#### 4. **Quick Actions**
- View All Orders
- Filter Pending Orders
- Filter Ready to Ship
- Quick access to common tasks

#### 5. **Supplier Information**
- Company name
- Contact person
- Phone and email
- Cannot be edited (contact admin to update)

### Navigation

From dashboard, suppliers can:
- View all orders
- Filter by status
- Access individual orders
- Logout

---

## Managing Orders

### Viewing All Orders

**URL**: `/supplier/orders/`

Features:
- **Complete Order List**: All orders for this supplier
- **Status Filters**: Filter by order status
- **Pagination**: 20 orders per page
- **Quick Actions**: Approve or view buttons
- **Sorting**: Most recent first

### Viewing Order Details

**URL**: `/supplier/orders/<order_id>/`

Details Displayed:
- Order number and status
- Customer information (limited)
- Order date
- Expected delivery date
- Total amount
- Complete item list with quantities and prices
- QR code for shipment
- Available actions based on status

### Available Actions by Status

#### Pending Orders
- ✅ **Approve Order**
- ❌ View only

#### Approved Orders
- ✅ **Mark as Shipped**
- ✅ View/Print QR Code

#### Shipped Orders
- ✅ View/Track
- ✅ Print QR Code
- ⏳ Wait for customer receipt

#### Received Orders
- ✅ View only (completed)
- ✅ View history

---

## Order Workflow

### Step 1: Receive Order Notification

When staff creates a purchase order:
1. Order appears in supplier dashboard
2. Status: **Pending**
3. Supplier receives notification (if email enabled)

### Step 2: Review Order

Supplier reviews:
- Items requested
- Quantities
- Prices
- Delivery date requested
- Special instructions

### Step 3: Approve Order

**URL**: `/supplier/orders/<order_id>/approve/`

Process:
1. Click "Approve Order" button
2. Set **Expected Delivery Date**
3. Add **Supplier Notes** (optional)
4. Click "Approve Order"

What Happens:
- Order status → "Approved"
- Timestamp recorded
- Customer notified (if email enabled)
- QR code becomes active

### Step 4: Prepare Shipment

Supplier:
1. Prepares items
2. Prints QR code from order detail page
3. Attaches QR code to package
4. Prepares shipping documents

### Step 5: Ship Order

When ready to ship:
1. Open order detail page
2. Click "Mark as Shipped"
3. Order status → "Shipped"
4. Customer notified

### Step 6: Customer Receives

Customer:
1. Scans QR code on delivery
2. Order status → "Received"
3. Items automatically added to inventory
4. Supplier dashboard updated

---

## Technical Details

### Database Changes

#### User Model Extensions

```python
# New fields added to User model
role = models.CharField(choices=ROLE_CHOICES)
    # New choice: 'supplier'

supplier = models.OneToOneField(
    'Supplier',
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)
```

#### New Methods

```python
User.is_supplier_user()
# Returns: True if user is a supplier account

User.get_supplier_orders()
# Returns: QuerySet of orders for this supplier
```

### URL Routes

```python
# Supplier Portal Routes
/supplier/login/                     # Supplier login page
/supplier/dashboard/                 # Supplier dashboard
/supplier/orders/                    # List all supplier orders
/supplier/orders/<id>/               # Order detail
/supplier/orders/<id>/approve/       # Approve order
/supplier/orders/<id>/ship/          # Mark as shipped
```

### Security Decorators

```python
@supplier_required
# Ensures user is a supplier account

@supplier_or_admin_required
# Allows supplier OR admin access
```

### Views

- `supplier_login`: Custom login for suppliers
- `supplier_dashboard`: Dashboard overview
- `supplier_orders`: List orders
- `supplier_order_detail`: View order details
- `supplier_order_approve`: Approve orders
- `supplier_order_ship`: Mark as shipped

### Templates

- `supplier_login.html`: Dedicated login page
- `supplier_dashboard.html`: Dashboard
- `supplier_orders.html`: Order list
- `supplier_order_detail.html`: Order details
- `supplier_order_approve.html`: Approval form

---

## Use Cases

### Use Case 1: New Order

**Scenario**: Staff creates a new purchase order

**Supplier Flow**:
1. Login to supplier portal
2. See new pending order on dashboard
3. Review order details
4. Approve with delivery date
5. Prepare items

### Use Case 2: Shipping Order

**Scenario**: Items are ready to ship

**Supplier Flow**:
1. Login to supplier portal
2. Open approved order
3. Print QR code
4. Attach to package
5. Mark as shipped

### Use Case 3: Check Status

**Scenario**: Customer asks about order status

**Supplier Flow**:
1. Login to supplier portal
2. Search for order number
3. View current status
4. Check delivery date
5. Provide update to customer

### Use Case 4: Review History

**Scenario**: Need to check past orders

**Supplier Flow**:
1. Login to supplier portal
2. View all orders
3. Filter by received status
4. Review completed orders
5. Check payment records

---

## Troubleshooting

### Issue 1: Cannot Login

**Problem**: Supplier cannot access portal

**Solutions**:
- Verify using correct login URL: `/supplier/login/`
- Check username/password
- Ensure account role is "supplier"
- Verify account is active
- Check supplier link is set

### Issue 2: No Orders Visible

**Problem**: Supplier sees no orders

**Solutions**:
- Verify supplier link in user account
- Check if orders exist for this supplier
- Verify orders are not cancelled
- Clear browser cache
- Check date filters

### Issue 3: Cannot Approve Order

**Problem**: Approve button not working

**Solutions**:
- Verify order status is "pending"
- Check expected delivery date is set
- Ensure user has supplier role
- Check order belongs to this supplier
- Review browser console for errors

### Issue 4: QR Code Not Printing

**Problem**: QR code won't print

**Solutions**:
- Use browser print function
- Check printer settings
- Try different browser
- Download QR code image
- Use print-friendly view

---

## Best Practices

### For Suppliers

1. **Login Regularly**: Check portal daily for new orders
2. **Approve Quickly**: Process orders within 24 hours
3. **Update Delivery Dates**: Be realistic with estimates
4. **Add Notes**: Communicate any issues early
5. **Print QR Codes**: Always attach to shipments
6. **Mark Shipped**: Update status immediately
7. **Keep Records**: Download/print important orders

### For Administrators

1. **Create Accounts Properly**: Link to supplier record
2. **Set Strong Passwords**: Use secure passwords
3. **Provide Training**: Show suppliers how to use portal
4. **Monitor Usage**: Check supplier login activity
5. **Respond Quickly**: Answer supplier questions
6. **Update Contact Info**: Keep supplier data current
7. **Test Regularly**: Verify portal functionality

---

## Benefits

### For Suppliers

✅ **24/7 Access**: View orders anytime  
✅ **Real-Time Updates**: See order status instantly  
✅ **Self-Service**: Manage orders independently  
✅ **Better Communication**: Direct system access  
✅ **Reduced Errors**: No manual data entry  
✅ **Order History**: Complete records available  
✅ **Professional Image**: Modern online portal  

### For Your Business

✅ **Faster Processing**: Suppliers approve immediately  
✅ **Better Data**: Accurate delivery dates  
✅ **Reduced Calls**: Less back-and-forth communication  
✅ **Audit Trail**: Complete action history  
✅ **Accountability**: Suppliers responsible for updates  
✅ **Scalability**: Handle more suppliers easily  
✅ **Professional**: Modern B2B system  

---

## Future Enhancements

Potential improvements:

1. **Email Notifications**
   - Automatic emails on order creation
   - Shipping confirmations
   - Delivery reminders

2. **Mobile App**
   - Native iOS/Android apps
   - Push notifications
   - Camera QR scanning

3. **Partial Shipments**
   - Split orders into multiple shipments
   - Track partial deliveries
   - Update quantities

4. **Invoice Integration**
   - Generate invoices automatically
   - Payment tracking
   - Receipt management

5. **Performance Analytics**
   - Delivery time metrics
   - Order accuracy rates
   - Supplier scorecards

6. **Chat System**
   - In-app messaging
   - Order discussions
   - File attachments

---

## Support

### For Suppliers

If you need help:
1. Check this documentation
2. Contact your main contact person
3. Email support address
4. Call main office

### For Staff

If suppliers need help:
1. Review their account setup
2. Check supplier link in admin
3. Verify order visibility
4. Test login yourself
5. Check audit logs

---

## Security Notes

### Access Control

- Suppliers can only see their own orders
- Cannot access other supplier data
- Cannot view inventory details
- Cannot access staff functions
- Cannot modify prices or items

### Data Privacy

- Limited customer information shown
- No access to other suppliers
- Audit trail of all actions
- Secure password requirements
- Session timeout protection

### Best Practices

- Change default passwords
- Don't share accounts
- Logout after use
- Report suspicious activity
- Use secure connections (HTTPS)

---

## Quick Reference

### Common URLs

| Page | URL | Access |
|------|-----|--------|
| Supplier Login | `/supplier/login/` | Public |
| Dashboard | `/supplier/dashboard/` | Supplier Only |
| All Orders | `/supplier/orders/` | Supplier Only |
| Order Detail | `/supplier/orders/<id>/` | Supplier Only |
| Approve Order | `/supplier/orders/<id>/approve/` | Supplier Only |

### Order Statuses

| Status | Supplier Action | Next Step |
|--------|----------------|-----------|
| Pending | Approve Order | Sets to Approved |
| Approved | Mark as Shipped | Sets to Shipped |
| Shipped | Wait | Customer receives |
| Received | View Only | Completed |

### Support Contacts

- **Technical Issues**: admin@yoursystem.com
- **Account Questions**: contact@yoursystem.com
- **Order Questions**: orders@yoursystem.com

---

## Changelog

**Version 1.0** (October 2025)
- Initial supplier portal release
- Dashboard and order management
- Approve and ship functionality
- QR code integration
- Complete audit trail

---

**Document Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: ✅ Production Ready

