#!/usr/bin/env python
"""Test script to check recipe and ingredients"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
django.setup()

from inventory.models import Item, Recipe, RecipeItem

print("=" * 50)
print("RECIPE TEST SCRIPT")
print("=" * 50)

# Check ingredients
ingredients = Item.objects.filter(category='ingredient', is_active=True)
print(f"\n1. Total Ingredients in database: {ingredients.count()}")
if ingredients.count() > 0:
    print("   Sample ingredients:")
    for ing in ingredients[:5]:
        print(f"   - {ing.name} ({ing.code})")
else:
    print("   ⚠️  NO INGREDIENTS FOUND! You need to create ingredients first.")

# Check finished goods
finished_goods = Item.objects.filter(category='finished_good', is_active=True)
print(f"\n2. Total Finished Goods in database: {finished_goods.count()}")
if finished_goods.count() > 0:
    print("   Sample finished goods:")
    for fg in finished_goods[:5]:
        print(f"   - {fg.name} ({fg.code})")
else:
    print("   ⚠️  NO FINISHED GOODS FOUND! You need to create finished goods first.")

# Check recipes
recipes = Recipe.objects.all()
print(f"\n3. Total Recipes in database: {recipes.count()}")
if recipes.count() > 0:
    print("\n   Recipe Details:")
    for recipe in recipes:
        recipe_items = RecipeItem.objects.filter(recipe=recipe)
        print(f"\n   📖 Recipe: {recipe.name}")
        print(f"      Product: {recipe.product.name}")
        print(f"      Yield: {recipe.yield_qty} {recipe.get_yield_unit_display()}")
        print(f"      Ingredients: {recipe_items.count()}")
        if recipe_items.count() > 0:
            for item in recipe_items:
                print(f"         - {item.ingredient.name}: {item.qty} {item.get_unit_display()}")
        else:
            print(f"         ⚠️  NO INGREDIENTS LINKED TO THIS RECIPE!")
        if recipe.steps:
            print(f"      Steps: {recipe.steps[:100]}...")
        else:
            print(f"      Steps: (none)")
else:
    print("   No recipes found yet.")

print("\n" + "=" * 50)
print("RECOMMENDATIONS:")
print("=" * 50)

if ingredients.count() == 0:
    print("1. Create ingredients first (Items → Create Item → Category: Ingredient)")
    print("   Examples: Flour, Butter, Sugar, Salt, Eggs, Milk")

if finished_goods.count() == 0:
    print("2. Create finished goods (Items → Create Item → Category: Finished Good)")
    print("   Examples: Croissant, Bread, Cake, Pastry")

if recipes.count() == 0:
    print("3. Create a recipe (Recipes → New Recipe)")
elif RecipeItem.objects.count() == 0:
    print("3. ⚠️  Recipes exist but have NO ingredients!")
    print("   This means the ingredient data is not being saved properly.")
    print("   Check the browser console for JavaScript errors.")

print("\n" + "=" * 50)
