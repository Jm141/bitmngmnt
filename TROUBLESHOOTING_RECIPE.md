# Recipe Ingredients Not Saving - Troubleshooting Guide

## Problem
When creating a recipe, the recipe is saved but ingredients are not being linked to it.

## Diagnostic Steps

### Step 1: Run the Test Script
```bash
python test_recipe.py
```

This will show:
- How many ingredients exist in the database
- How many finished goods exist
- How many recipes exist and their ingredient counts

### Step 2: Check Browser Console
1. Open the recipe creation page
2. Press F12 to open Developer Tools
3. Go to the Console tab
4. Look for these messages when the page loads:
   ```
   Elements found: {container: true, button: true, template: true, hiddenInput: true, form: true}
   ```
5. Fill in the recipe form and add ingredients
6. Click "Save Recipe"
7. Look for these messages:
   ```
   Form submitting, found rows: 1 (or more)
   Row data: {ingredient: "uuid", qty: "500", unit: "g"}
   Ingredients JSON: [{"ingredient_id":"uuid","qty":500,"unit":"g"}]
   Hidden field value set: [{"ingredient_id":"uuid","qty":500,"unit":"g"}]
   ```

### Step 3: Check Server Logs
When you submit the form, check the terminal running the Django server for:
```
==================================================
POST DATA RECEIVED:
  csrfmiddlewaretoken: ...
  name: Croissant
  product: uuid
  yield_qty: 10
  yield_unit: pcs
  description: ...
  steps: ...
  ingredients_data: [{"ingredient_id":"uuid","qty":500,"unit":"g"}]
==================================================
Ingredients data received: '[{"ingredient_id":"uuid","qty":500,"unit":"g"}]'
```

## Common Issues and Solutions

### Issue 1: Hidden Input Field Not Found
**Symptom**: Console shows `hiddenInput: false`
**Solution**: The form field `ingredients_data` is not rendering properly
- Check that `RecipeForm` includes `ingredients_data` field
- Verify the template includes `{{ form.ingredients_data }}`

### Issue 2: No Ingredients in Database
**Symptom**: Test script shows "Total Ingredients: 0"
**Solution**: Create ingredients first
1. Go to Items → Create Item
2. Set Category to "Ingredient"
3. Create items like: Flour, Butter, Sugar, Salt, etc.

### Issue 3: No Finished Goods
**Symptom**: Product dropdown is empty
**Solution**: Create finished goods first
1. Go to Items → Create Item
2. Set Category to "Finished Good"
3. Create items like: Croissant, Bread, Cake, etc.

### Issue 4: JavaScript Not Running
**Symptom**: No console logs appear
**Solution**: JavaScript error preventing execution
- Check browser console for errors (red messages)
- Look for syntax errors in recipe_form.html

### Issue 5: POST Data Missing ingredients_data
**Symptom**: Server logs show no `ingredients_data` in POST
**Solution**: JavaScript not setting the hidden field
- Verify the form submit event listener is attached
- Check that `ingredientsDataInput.value` is being set
- Ensure form is not submitting before JavaScript runs

### Issue 6: JSON Parse Error
**Symptom**: Server logs show "Error adding ingredients: ..."
**Solution**: Invalid JSON format
- Check the JSON structure in console logs
- Verify all required fields (ingredient_id, qty, unit) are present

## Manual Test

If automated tests fail, try this manual test:

1. Open recipe creation page
2. Open browser console (F12)
3. Add one ingredient manually
4. Before clicking Save, run this in console:
   ```javascript
   document.getElementById('id_ingredients_data').value = '[{"ingredient_id":"PASTE_REAL_UUID_HERE","qty":500,"unit":"g"}]';
   ```
5. Click Save Recipe
6. Check if ingredient appears in recipe detail page

## Quick Fix Attempt

If nothing works, try creating a recipe via Django admin:
1. Go to `/admin/`
2. Create a Recipe
3. Create RecipeItems linked to that recipe
4. Verify they appear in the recipe detail page

This will confirm if the issue is with the form/JavaScript or the backend logic.

## Files to Check

1. `inventory/models.py` - Recipe and RecipeItem models
2. `inventory/forms.py` - RecipeForm with ingredients_data field
3. `inventory/views.py` - recipe_create view with JSON parsing
4. `inventory/templates/inventory/recipe_form.html` - Form and JavaScript
5. `inventory/templates/inventory/recipe_detail.html` - Display logic

## Contact

If issue persists after all checks, provide:
1. Browser console logs (screenshot)
2. Server terminal output (copy/paste)
3. Test script output
4. Browser and version
