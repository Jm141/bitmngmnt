"""
Inventory management services for FEFO/FIFO logic and stock calculations
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Item, StockLot, StockMovement, Recipe, RecipeItem, Supplier


class InventoryService:
    """
    Service class for inventory management operations
    """
    
    @staticmethod
    def get_available_lots(item, qty_needed=None):
        """
        Get available stock lots for an item using FEFO (First Expiry, First Out) logic
        Falls back to FIFO (First In, First Out) for non-perishable items
        """
        if item.is_perishable:
            # FEFO: Order by expiry date (earliest first), then by received date
            lots = StockLot.objects.filter(
                item=item,
                qty__gt=0
            ).order_by('expires_at', 'received_at')
        else:
            # FIFO: Order by received date (earliest first)
            lots = StockLot.objects.filter(
                item=item,
                qty__gt=0
            ).order_by('received_at')
        
        if qty_needed:
            # Filter lots that have enough quantity
            available_lots = []
            remaining_qty = qty_needed
            
            for lot in lots:
                if remaining_qty <= 0:
                    break
                if lot.qty > 0:
                    available_lots.append(lot)
                    remaining_qty -= lot.qty
            
            return available_lots
        
        return lots
    
    @staticmethod
    def calculate_consumption_lots(item, qty_needed):
        """
        Calculate which lots to consume and how much from each lot
        Returns list of tuples: (lot, qty_to_consume)
        """
        lots = InventoryService.get_available_lots(item, qty_needed)
        consumption_plan = []
        remaining_qty = qty_needed
        
        for lot in lots:
            if remaining_qty <= 0:
                break
            
            if lot.qty > 0:
                qty_to_consume = min(lot.qty, remaining_qty)
                consumption_plan.append((lot, qty_to_consume))
                remaining_qty -= qty_to_consume
        
        if remaining_qty > 0:
            raise ValueError(f"Insufficient stock. Need {qty_needed}, available {qty_needed - remaining_qty}")
        
        return consumption_plan
    
    @staticmethod
    @transaction.atomic
    def consume_stock(item, qty, reason, user, lot=None, ref_no=None, notes=None):
        """
        Consume stock from inventory
        """
        if lot:
            # Consume from specific lot
            if lot.qty < qty:
                raise ValueError(f"Insufficient stock in lot. Available: {lot.qty}")
            
            # Update lot quantity
            lot.qty -= qty
            lot.save()
            
            # Create movement record
            StockMovement.objects.create(
                item=item,
                lot=lot,
                movement_type='consume',
                qty=qty,
                unit=item.unit,
                reason=reason,
                ref_no=ref_no,
                notes=notes,
                created_by=user
            )
        else:
            # Auto-select lots using FEFO/FIFO
            consumption_plan = InventoryService.calculate_consumption_lots(item, qty)
            
            for lot, qty_to_consume in consumption_plan:
                # Update lot quantity
                lot.qty -= qty_to_consume
                lot.save()
                
                # Create movement record
                StockMovement.objects.create(
                    item=item,
                    lot=lot,
                    movement_type='consume',
                    qty=qty_to_consume,
                    unit=item.unit,
                    reason=reason,
                    ref_no=ref_no,
                    notes=notes,
                    created_by=user
                )
    
    @staticmethod
    @transaction.atomic
    def receive_stock(item, lot_no, qty, unit, user, supplier=None, expires_at=None, 
                     unit_cost=0, ref_no=None, notes=None):
        """
        Receive stock into inventory
        """
        # Create stock lot
        lot = StockLot.objects.create(
            item=item,
            lot_no=lot_no,
            qty=qty,
            unit=unit,
            expires_at=expires_at,
            unit_cost=unit_cost,
            supplier=supplier,
            notes=notes,
            created_by=user
        )
        
        # Create movement record
        StockMovement.objects.create(
            item=item,
            lot=lot,
            movement_type='receive',
            qty=qty,
            unit=unit,
            ref_no=ref_no,
            notes=notes,
            created_by=user
        )
        
        return lot
    
    @staticmethod
    @transaction.atomic
    def produce_stock(recipe, production_qty, lot_no, user, expires_at=None, notes=None):
        """
        Produce stock using recipe
        """
        # Calculate required ingredients
        required_ingredients = []
        for recipe_item in recipe.recipe_items.all():
            # Calculate quantity needed (including loss factor)
            qty_needed = float(recipe_item.qty) * float(production_qty) / float(recipe.yield_qty)
            qty_needed = qty_needed * recipe_item.get_adjusted_qty() / float(recipe_item.qty)
            
            required_ingredients.append({
                'ingredient': recipe_item.ingredient,
                'qty': qty_needed,
                'unit': recipe_item.unit
            })
        
        # Check if all ingredients are available
        for ingredient_data in required_ingredients:
            ingredient = ingredient_data['ingredient']
            qty_needed = ingredient_data['qty']
            
            available_stock = sum(lot.qty for lot in InventoryService.get_available_lots(ingredient))
            if available_stock < qty_needed:
                raise ValueError(f"Insufficient stock for {ingredient.name}. Need: {qty_needed}, Available: {available_stock}")
        
        # Consume ingredients
        for ingredient_data in required_ingredients:
            ingredient = ingredient_data['ingredient']
            qty_needed = ingredient_data['qty']
            
            InventoryService.consume_stock(
                item=ingredient,
                qty=qty_needed,
                reason=f"Production: {recipe.name}",
                user=user,
                ref_no=f"PROD-{recipe.id}",
                notes=f"Used in production of {recipe.product.name}"
            )
        
        # Create produced stock lot
        produced_lot = StockLot.objects.create(
            item=recipe.product,
            lot_no=lot_no,
            qty=production_qty,
            unit=recipe.yield_unit,
            expires_at=expires_at,
            notes=notes,
            created_by=user
        )
        
        # Create movement record for production
        StockMovement.objects.create(
            item=recipe.product,
            lot=produced_lot,
            movement_type='produce',
            qty=production_qty,
            unit=recipe.yield_unit,
            ref_no=f"PROD-{recipe.id}",
            notes=f"Produced using recipe: {recipe.name}",
            created_by=user
        )
        
        return produced_lot
    
    @staticmethod
    @transaction.atomic
    def adjust_stock(item, qty, reason, user, lot=None, ref_no=None, notes=None):
        """
        Adjust stock (increase or decrease)
        """
        if lot:
            # Adjust specific lot
            lot.qty += qty
            if lot.qty < 0:
                raise ValueError("Lot quantity cannot be negative")
            lot.save()
        else:
            # For negative adjustments, consume from available lots
            if qty < 0:
                InventoryService.consume_stock(
                    item=item,
                    qty=abs(qty),
                    reason=reason,
                    user=user,
                    ref_no=ref_no,
                    notes=notes
                )
                return
            
            # For positive adjustments, create new lot
            lot_no = f"ADJ-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
            lot = StockLot.objects.create(
                item=item,
                lot_no=lot_no,
                qty=qty,
                unit=item.unit,
                notes=notes,
                created_by=user
            )
        
        # Create movement record
        StockMovement.objects.create(
            item=item,
            lot=lot,
            movement_type='adjust',
            qty=qty,
            unit=item.unit,
            reason=reason,
            ref_no=ref_no,
            notes=notes,
            created_by=user
        )
    
    @staticmethod
    def get_low_stock_items():
        """
        Get items that are below reorder level
        """
        low_stock_items = []
        items = Item.objects.filter(is_active=True)
        
        for item in items:
            current_stock = item.get_current_stock()
            if current_stock <= item.reorder_level:
                low_stock_items.append({
                    'item': item,
                    'current_stock': current_stock,
                    'reorder_level': item.reorder_level,
                    'shortage': item.reorder_level - current_stock
                })
        
        return low_stock_items
    
    @staticmethod
    def get_expiring_items(days=7):
        """
        Get items expiring within specified days
        """
        expiry_date = timezone.now().date() + timedelta(days=days)
        
        expiring_lots = StockLot.objects.filter(
            qty__gt=0,
            expires_at__lte=expiry_date,
            expires_at__isnull=False
        ).select_related('item').order_by('expires_at')
        
        return expiring_lots
    
    @staticmethod
    def get_expired_items():
        """
        Get expired items
        """
        today = timezone.now().date()
        
        expired_lots = StockLot.objects.filter(
            qty__gt=0,
            expires_at__lt=today,
            expires_at__isnull=False
        ).select_related('item').order_by('expires_at')
        
        return expired_lots
    
    @staticmethod
    def calculate_item_cost(item):
        """
        Calculate weighted average cost for an item
        """
        lots = StockLot.objects.filter(item=item, qty__gt=0)
        
        if not lots.exists():
            return Decimal('0.00')
        
        total_cost = Decimal('0.00')
        total_qty = Decimal('0.00')
        
        for lot in lots:
            total_cost += lot.qty * lot.unit_cost
            total_qty += lot.qty
        
        if total_qty > 0:
            return total_cost / total_qty
        
        return Decimal('0.00')
    
    @staticmethod
    def get_stock_summary():
        """
        Get overall stock summary
        """
        items = Item.objects.filter(is_active=True)
        total_items = items.count()
        low_stock_count = len(InventoryService.get_low_stock_items())
        expiring_count = InventoryService.get_expiring_items().count()
        expired_count = InventoryService.get_expired_items().count()
        
        return {
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'expiring_count': expiring_count,
            'expired_count': expired_count
        }


class RecipeService:
    """
    Service class for recipe management
    """
    
    @staticmethod
    def calculate_recipe_cost(recipe):
        """
        Calculate total cost of a recipe
        """
        total_cost = Decimal('0.00')
        
        for recipe_item in recipe.recipe_items.all():
            ingredient_cost = InventoryService.calculate_item_cost(recipe_item.ingredient)
            qty_with_loss = recipe_item.get_adjusted_qty()
            total_cost += Decimal(str(qty_with_loss)) * ingredient_cost
        
        return total_cost
    
    @staticmethod
    def validate_recipe_production(recipe, production_qty):
        """
        Validate if recipe can be produced with current stock
        """
        validation_result = {
            'can_produce': True,
            'missing_ingredients': [],
            'total_cost': Decimal('0.00')
        }
        
        for recipe_item in recipe.recipe_items.all():
            # Calculate quantity needed
            qty_needed = float(recipe_item.qty) * float(production_qty) / float(recipe.yield_qty)
            qty_needed = qty_needed * recipe_item.get_adjusted_qty() / float(recipe_item.qty)
            
            # Check available stock
            available_stock = sum(lot.qty for lot in InventoryService.get_available_lots(recipe_item.ingredient))
            
            if available_stock < qty_needed:
                validation_result['can_produce'] = False
                validation_result['missing_ingredients'].append({
                    'ingredient': recipe_item.ingredient,
                    'needed': qty_needed,
                    'available': available_stock,
                    'shortage': qty_needed - available_stock
                })
            
            # Calculate cost
            ingredient_cost = InventoryService.calculate_item_cost(recipe_item.ingredient)
            validation_result['total_cost'] += Decimal(str(qty_needed)) * ingredient_cost
        
        return validation_result
