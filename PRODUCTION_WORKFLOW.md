# Production Workflow - Auto Ingredient Consumption

## ✅ System Already Implemented!

The production system **automatically calculates and consumes ingredients** based on the recipe yield and production quantity.

## How It Works

### Step-by-Step Process

#### 1. **Recipe Setup**
```
Recipe: Croissant
Yield: 10 pieces
Ingredients:
  - Flour: 500g
  - Butter: 250g
  - Sugar: 50g
  - Salt: 10g
```

#### 2. **Production Request**
```
User wants to produce: 50 pieces of Croissant
```

#### 3. **Auto-Calculation**
The system automatically calculates:
```python
# Formula: (ingredient_qty × production_qty) ÷ recipe_yield_qty

Production Quantity: 50 pieces
Recipe Yield: 10 pieces
Multiplier: 50 ÷ 10 = 5x

Required Ingredients:
  - Flour: 500g × 5 = 2,500g (2.5kg)
  - Butter: 250g × 5 = 1,250g (1.25kg)
  - Sugar: 50g × 5 = 250g
  - Salt: 10g × 5 = 50g
```

#### 4. **Stock Validation**
Before production starts, system checks:
```
✓ Flour: Need 2,500g → Available: 5,000g ✓
✓ Butter: Need 1,250g → Available: 2,000g ✓
✓ Sugar: Need 250g → Available: 500g ✓
✓ Salt: Need 50g → Available: 100g ✓

All ingredients available → Production can proceed
```

If ANY ingredient is insufficient:
```
✗ Flour: Need 2,500g → Available: 1,000g ✗

ERROR: Cannot produce!
Message: "Insufficient stock for Flour. Need: 2500g, Available: 1000g"
Production is BLOCKED
```

#### 5. **Auto-Consumption**
Once validated, system automatically:
```
1. Deducts from stock:
   - Flour: 5,000g → 2,500g (consumed 2,500g)
   - Butter: 2,000g → 750g (consumed 1,250g)
   - Sugar: 500g → 250g (consumed 250g)
   - Salt: 100g → 50g (consumed 50g)

2. Records movements:
   - Type: "consume"
   - Reason: "Production: Croissant"
   - Reference: "PROD-{recipe_id}"
   - Notes: "Used in production of Croissant"

3. Creates finished goods:
   - Item: Croissant
   - Quantity: 50 pieces
   - Lot Number: LOT-20251020-2100
   - Unit Cost: ₱0.76 per piece (auto-calculated)

4. Records production:
   - Type: "produce"
   - Reference: "PROD-{recipe_id}"
   - Notes: "Produced using recipe: Croissant"
```

## Code Implementation

### Location: `inventory/services.py` → `produce_stock()`

```python
@transaction.atomic
def produce_stock(recipe, production_qty, lot_no, user, ...):
    # Step 1: Calculate required ingredients
    for recipe_item in recipe.recipe_items.all():
        qty_needed = (recipe_item.qty × production_qty) ÷ recipe.yield_qty
        
    # Step 2: Validate stock availability
    for ingredient in required_ingredients:
        if available_stock < qty_needed:
            raise ValueError("Insufficient stock!")
    
    # Step 3: Auto-consume ingredients
    for ingredient in required_ingredients:
        InventoryService.consume_stock(
            item=ingredient,
            qty=qty_needed,
            reason=f"Production: {recipe.name}"
        )
    
    # Step 4: Create finished goods
    produced_lot = StockLot.objects.create(
        item=recipe.product,
        qty=production_qty,
        unit_cost=unit_cost
    )
```

## Example Scenarios

### Scenario 1: Normal Production
```
Recipe: Croissant (yields 10 pcs)
  - Flour: 500g
  - Butter: 250g

Production: 20 pieces

Calculation:
  - Multiplier: 20 ÷ 10 = 2x
  - Flour needed: 500g × 2 = 1,000g
  - Butter needed: 250g × 2 = 500g

Result:
  ✓ Ingredients auto-consumed
  ✓ 20 croissants added to stock
```

### Scenario 2: Large Batch
```
Recipe: Croissant (yields 10 pcs)
  - Flour: 500g
  - Butter: 250g

Production: 100 pieces

Calculation:
  - Multiplier: 100 ÷ 10 = 10x
  - Flour needed: 500g × 10 = 5,000g (5kg)
  - Butter needed: 250g × 10 = 2,500g (2.5kg)

Result:
  ✓ Ingredients auto-consumed
  ✓ 100 croissants added to stock
```

### Scenario 3: Fractional Production
```
Recipe: Croissant (yields 10 pcs)
  - Flour: 500g
  - Butter: 250g

Production: 5 pieces (half batch)

Calculation:
  - Multiplier: 5 ÷ 10 = 0.5x
  - Flour needed: 500g × 0.5 = 250g
  - Butter needed: 250g × 0.5 = 125g

Result:
  ✓ Ingredients auto-consumed
  ✓ 5 croissants added to stock
```

### Scenario 4: Insufficient Stock
```
Recipe: Croissant (yields 10 pcs)
  - Flour: 500g (Available: 300g)
  - Butter: 250g (Available: 500g)

Production: 10 pieces

Validation:
  ✗ Flour: Need 500g, Available 300g
  
Result:
  ✗ Production BLOCKED
  ✗ Error message shown
  ✗ NO ingredients consumed
  ✗ NO finished goods created
```

## Features

### ✅ Automatic Calculation
- System calculates exact ingredient quantities
- Based on recipe yield ratio
- Supports any production quantity

### ✅ Stock Validation
- Checks availability BEFORE production
- Prevents production if insufficient
- Shows exactly what's missing

### ✅ Atomic Transaction
- All-or-nothing operation
- If any step fails, everything rolls back
- No partial consumption

### ✅ Complete Audit Trail
- Every ingredient consumption logged
- Production movements recorded
- User tracking for accountability

### ✅ Cost Tracking
- Auto-calculates unit cost from ingredients
- Or manually set cost (includes labor/overhead)
- Stored with each production lot

### ✅ Loss Factor Support
- Recipe can include loss factor percentage
- System adjusts quantities automatically
- Accounts for waste/spillage

## Usage

### Creating Production

1. **Go to Production Page**:
   - Items → Click factory icon on finished good
   - Or: Recipes → View Recipe → "Create Production"

2. **Fill Form**:
   - Recipe: Select recipe
   - Quantity: Enter how many to produce
   - Unit Cost: Leave blank for auto-calc
   - Lot Number: Auto-generated
   - Expiration: Optional

3. **Submit**:
   - System validates ingredients
   - Auto-consumes from stock
   - Creates finished goods
   - Shows success message

### What Happens Behind the Scenes

```
User clicks "Start Production"
  ↓
System calculates ingredient needs
  ↓
Validates stock availability
  ↓
If insufficient → Show error, STOP
  ↓
If sufficient → Continue
  ↓
Deduct ingredients from stock
  ↓
Create finished goods lot
  ↓
Record all movements
  ↓
Show success message
```

## Benefits

✅ **No Manual Calculation** - System does the math
✅ **No Manual Deduction** - Auto-consumes ingredients
✅ **Prevents Errors** - Validates before production
✅ **Complete Tracking** - Full audit trail
✅ **Cost Accuracy** - Auto-calculates costs
✅ **Scalable** - Works for any batch size

## Notes

- Production is **irreversible** by design (for audit integrity)
- All calculations use **decimal precision** (no rounding errors)
- System uses **FIFO** (First In, First Out) for ingredient consumption
- **Transaction safety** ensures data consistency
- **User tracking** for all operations

## Future Enhancements

- [ ] Production scheduling
- [ ] Batch production (multiple recipes at once)
- [ ] Waste tracking and reporting
- [ ] Production efficiency metrics
- [ ] Cost variance analysis
- [ ] Ingredient substitution suggestions
