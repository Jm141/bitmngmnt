# Production Feature - Add Finished Goods with Pricing

## Overview
Added a production system to create finished goods from recipes with automatic ingredient consumption and cost tracking.

## What Was Added

### 1. Production Form with Pricing
**Location**: `inventory/forms.py` - `ProductionForm`

**Fields**:
- **Recipe**: Select which recipe to use
- **Quantity to Produce**: How many units to make
- **Unit Cost (₱)**: Price per unit (optional - auto-calculates if blank)
- **Lot Number**: Unique batch identifier (auto-generated)
- **Expiration Date**: For perishable products (optional)
- **Notes**: Production notes (optional)

### 2. Auto-Cost Calculation
**How it works**:
- If you leave "Unit Cost" blank, the system automatically calculates it from the recipe's ingredient costs
- Formula: `Total Ingredient Cost ÷ Recipe Yield Quantity = Unit Cost`
- You can also manually enter a cost to include labor, overhead, etc.

### 3. Production Workflow
**What happens when you produce**:
1. System checks if enough ingredients are in stock
2. If insufficient, shows error with missing ingredients
3. If sufficient:
   - Deducts ingredients from inventory
   - Creates a new stock lot for the finished product
   - Records the unit cost
   - Logs all movements

### 4. Access Production
**From Items List**:
- Go to **Items** page
- Look for finished goods
- Click the **factory icon** (🏭) button
- Opens production form

**From Recipe Detail**:
- View any recipe
- Click "Create Production" button

## How to Use

### Step 1: Create a Recipe (if not done)
1. Go to **Recipes** → **New Recipe**
2. Add recipe name, product, ingredients, steps
3. Save

### Step 2: Start Production
1. Go to **Items** page
2. Find your finished good
3. Click the **factory icon** button
4. Or go directly to `/inventory/production/create/`

### Step 3: Fill Production Form
- **Recipe**: Select "Croissant" (or your recipe)
- **Quantity**: Enter 50 (how many to produce)
- **Unit Cost**: Leave blank for auto-calc, or enter ₱25.00
- **Lot Number**: Auto-filled (e.g., LOT-20251020-2100)
- **Expiration**: Optional date
- **Notes**: Optional

### Step 4: Submit
- Click "Start Production"
- System validates ingredient availability
- If OK: Production completes, stock is added
- If not: Shows which ingredients are missing

## Example Scenario

**Recipe**: Croissant
- Yields: 10 pieces
- Ingredients:
  - Flour: 500g @ ₱5/kg = ₱2.50
  - Butter: 250g @ ₱20/kg = ₱5.00
  - Sugar: 50g @ ₱2/kg = ₱0.10
  - Salt: 10g @ ₱1/kg = ₱0.01
- **Total Cost**: ₱7.61
- **Cost per piece**: ₱0.76

**Production**:
- Quantity: 50 pieces (5x the recipe)
- Auto-calculated cost: ₱0.76 per piece
- Total value: ₱38.05

**Result**:
- Deducted from stock:
  - Flour: 2.5kg
  - Butter: 1.25kg
  - Sugar: 250g
  - Salt: 50g
- Added to stock:
  - Croissant: 50 pieces @ ₱0.76 each

## Features

### ✅ Automatic Ingredient Deduction
- No manual stock adjustments needed
- System calculates exact quantities based on recipe ratios
- Includes loss factor if specified in recipe

### ✅ Cost Tracking
- Auto-calculates from ingredient costs
- Or manually set to include overhead
- Stored with each production lot

### ✅ Lot Tracking
- Each production gets unique lot number
- Traceability for quality control
- Expiration date tracking

### ✅ Validation
- Checks ingredient availability before production
- Shows exactly what's missing
- Prevents production if insufficient stock

### ✅ Audit Trail
- All ingredient consumption logged
- Production movements recorded
- User tracking for accountability

## Files Modified/Created

### Modified:
1. `inventory/forms.py` - Added unit_cost field to ProductionForm
2. `inventory/views.py` - Updated production_create to handle unit_cost
3. `inventory/services.py` - Updated produce_stock to save unit_cost
4. `inventory/templates/inventory/item_list.html` - Added Produce button

### Created:
1. `inventory/templates/inventory/production_form.html` - Production form UI

## Future Enhancements

- [ ] Batch production (multiple recipes at once)
- [ ] Production scheduling
- [ ] Quality control checkpoints
- [ ] Waste tracking
- [ ] Production reports and analytics
- [ ] Cost variance analysis (actual vs. standard)

## Notes

- Production cannot be undone (by design for audit integrity)
- If you need to reverse, create a manual stock adjustment
- Unit cost is stored per lot, so different productions can have different costs
- The system uses FIFO (First In, First Out) for ingredient consumption
