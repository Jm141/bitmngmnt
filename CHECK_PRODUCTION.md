# Production Records Troubleshooting

## Where Production is Saved

Production records are saved in **TWO places**:

### 1. StockLot Table
- **Purpose**: Stores the finished goods inventory
- **Fields**: item, lot_no, qty, unit_cost, expires_at, notes
- **Created at**: Line 233-242 in `services.py`

### 2. StockMovement Table ⭐ (This is what we display)
- **Purpose**: Tracks all inventory movements including production
- **Fields**: item, lot, movement_type='produce', qty, unit, ref_no, notes, timestamp
- **Created at**: Line 245-254 in `services.py`
- **Query**: `StockMovement.objects.filter(movement_type='produce')`

## Why Nothing is Displaying - Possible Causes

### ✅ Check 1: Are there any production records?

**Run this in Django shell**:
```python
python manage.py shell

from inventory.models import StockMovement
productions = StockMovement.objects.filter(movement_type='produce')
print(f"Total production records: {productions.count()}")

# Show all production records
for p in productions:
    print(f"{p.timestamp} - {p.item.name} - {p.qty} {p.unit}")
```

### ✅ Check 2: Did production creation succeed?

**Check if you can create production**:
1. Go to `/production/`
2. Select a recipe
3. Enter quantity
4. Click "Create Production"
5. Check for success message
6. Check for any error messages

### ✅ Check 3: Check StockMovement table directly

**Run this SQL query**:
```sql
SELECT * FROM inventory_stockmovement WHERE movement_type = 'produce';
```

Or in Django shell:
```python
from inventory.models import StockMovement
StockMovement.objects.filter(movement_type='produce').values()
```

### ✅ Check 4: Verify the production_list view is being called

Add debug print in `views.py` at line 1419:
```python
productions = StockMovement.objects.filter(movement_type='produce')
print(f"DEBUG: Found {productions.count()} production records")
```

## Common Issues

### Issue 1: No Production Records Created Yet
**Solution**: Create a production first
- Go to `/production/`
- Fill out the form
- Submit

### Issue 2: Permission Error
**Solution**: Make sure user has `inventory_read` permission
- Check: User → Permissions → inventory_read ✓

### Issue 3: Empty QuerySet
**Possible causes**:
- Wrong movement_type (should be 'produce')
- Records exist but with different movement_type
- Database not synced

**Check all movement types**:
```python
from inventory.models import StockMovement
for mt in StockMovement.objects.values_list('movement_type', flat=True).distinct():
    count = StockMovement.objects.filter(movement_type=mt).count()
    print(f"{mt}: {count} records")
```

### Issue 4: Template Not Showing Data
**Check template logic**:
- Line 119: `{% if productions %}`
- If no productions, shows "No production records found"

## Quick Test

**Create a test production manually in Django shell**:
```python
python manage.py shell

from inventory.models import StockMovement, Item, StockLot, User
from django.utils import timezone

# Get a finished good item
item = Item.objects.filter(category='finished_good').first()
print(f"Using item: {item.name}")

# Get a user
user = User.objects.first()

# Create a stock lot
lot = StockLot.objects.create(
    item=item,
    lot_no='TEST-001',
    qty=10,
    unit='pcs',
    unit_cost=5.00,
    created_by=user
)

# Create production movement
production = StockMovement.objects.create(
    item=item,
    lot=lot,
    movement_type='produce',
    qty=10,
    unit='pcs',
    ref_no='TEST-PROD-001',
    notes='Test production',
    created_by=user
)

print(f"Created production: {production.id}")
print(f"Check at: /production/list/")
```

## Verification Steps

1. **Check if production records exist**:
   ```python
   StockMovement.objects.filter(movement_type='produce').count()
   ```

2. **Check if page loads**:
   - Visit `/production/list/`
   - Should see page without errors

3. **Check if data displays**:
   - If count > 0 but nothing shows: Template issue
   - If count = 0: No production created yet

4. **Check today's production**:
   ```python
   from django.utils import timezone
   today = timezone.now().date()
   StockMovement.objects.filter(
       movement_type='produce',
       timestamp__date=today
   ).count()
   ```

## Expected Behavior

**After creating production**:
1. Success message appears
2. Redirected to item detail page
3. Production appears in `/production/list/`
4. Production appears in staff dashboard (if today)
5. StockMovement record created with movement_type='produce'
6. StockLot record created with finished goods

## Next Steps

1. Run the Django shell checks above
2. Try creating a new production
3. Check if it appears in the list
4. If still not showing, share the output of:
   ```python
   StockMovement.objects.filter(movement_type='produce').count()
   ```
