# Auto-Generated Item Code Feature

## Summary
Item codes are now automatically generated in the format `YYYYMM0001` where:
- `YYYY` = Current year (e.g., 2025)
- `MM` = Current month (e.g., 10 for October)
- `0001` = Sequential number (resets each month)

## Changes Made

### 1. Updated `inventory/models.py` - Item Model

**Modified Fields:**
- `code` field now allows `blank=True` to enable auto-generation

**New Methods:**

#### `generate_item_code()` (Static Method)
```python
@staticmethod
def generate_item_code():
    """Generate item code in format YYYYMM0001"""
```
- Gets current date prefix (YYYYMM)
- Finds the last item code with the same prefix
- Increments the numeric part
- Returns formatted code (e.g., 2025100001)

#### `save()` (Overridden)
```python
def save(self, *args, **kwargs):
    # Auto-generate code if not provided (new item)
    if not self.code:
        self.code = self.generate_item_code()
    super().save(*args, **kwargs)
```
- Automatically generates code before saving if code is empty
- Preserves existing codes when updating items

### 2. Updated `inventory/forms.py` - ItemForm

**Removed Fields:**
- Removed `'code'` from the fields list
- Removed code widget from widgets dictionary

**Updated Comment:**
```python
"""
Form for managing items (code is auto-generated)
"""
```

### 3. Database Migration

**Migration:** `0005_auto_generate_item_code.py`
- Alters the `code` field to allow blank values
- Applied successfully to database

## Code Format Examples

| Month/Year | First Item | Second Item | Third Item |
|------------|-----------|-------------|------------|
| Oct 2025   | 2025100001 | 2025100002 | 2025100003 |
| Nov 2025   | 2025110001 | 2025110002 | 2025110003 |
| Dec 2025   | 2025120001 | 2025120002 | 2025120003 |
| Jan 2026   | 2026010001 | 2026010002 | 2026010003 |

## Testing Results

✅ **Test 1:** First item creation
```
Generated code: 2025100001
```

✅ **Test 2:** Sequential increment
```
Generated code: 2025100002
```

## User Interface Changes

### Before:
- Item creation form had a **Code** input field
- User had to manually enter item codes
- Risk of duplicate codes or inconsistent formatting

### After:
- Item creation form **no longer shows** the Code field
- Code is automatically generated on save
- Consistent formatting across all items
- Sequential numbering by month

## How It Works

1. User navigates to **Create Item** page
2. User fills in item details (name, category, unit, etc.)
3. User **does not** enter a code (field is hidden)
4. When the form is submitted:
   - The `Item.save()` method checks if code is empty
   - If empty, calls `generate_item_code()`
   - Queries database for last item code with current month prefix
   - Increments the number and formats it
   - Saves the item with the generated code

## Benefits

1. **Consistency**: All item codes follow the same format
2. **No Duplicates**: System ensures unique codes
3. **Time-Saving**: No manual code entry required
4. **Organization**: Easy to identify items by creation month
5. **Scalability**: Supports up to 9,999 items per month

## Important Notes

- **Sequential numbering resets each month** (starts at 0001)
- **Existing items** retain their original codes
- **Updates to existing items** don't change their codes
- **Code format is fixed**: Cannot be customized per item
- **Maximum items per month**: 9,999 (0001-9999)

## Future Enhancements

Possible improvements:
1. Add prefix based on category (e.g., ING-2025100001 for ingredients)
2. Allow custom code format in settings
3. Add code preview before saving
4. Show generated code after creation
5. Support for different numbering schemes (daily, yearly, etc.)

## Troubleshooting

**Q: What if I need to create more than 9,999 items in a month?**
A: The 4-digit format supports up to 9,999 items. If needed, modify the `generate_item_code()` method to use 5 digits (`{new_number:05d}`).

**Q: Can I manually set a code?**
A: Currently, the form doesn't allow manual code entry. If needed for special cases, you can set it via Django admin or shell.

**Q: What happens on the 1st of each month?**
A: The numbering automatically resets to 0001 for the new month (e.g., 2025110001 for November).

**Q: Will this affect existing items?**
A: No, existing items keep their current codes. Only new items get auto-generated codes.

