"""
Inventory management services for FEFO/FIFO logic and stock calculations
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Item, StockLot, StockMovement, Recipe, RecipeItem, Supplier, PurchaseOrder, PurchaseOrderItem


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
            remaining_qty = Decimal(str(qty_needed))
            
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
        remaining_qty = Decimal(str(qty_needed))
        
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
        Consume stock from inventory with automatic overflow to next lots
        """
        qty = Decimal(str(qty))
        remaining_qty = qty
        
        if lot:
            # Start consuming from specific lot, overflow to next lots if needed
            # First, consume what we can from the selected lot
            qty_from_selected = min(lot.qty, remaining_qty)
            
            if qty_from_selected > 0:
                lot.qty -= qty_from_selected
                lot.save()
                
                # Create movement record for selected lot
                StockMovement.objects.create(
                    item=item,
                    lot=lot,
                    movement_type='consume',
                    qty=qty_from_selected,
                    unit=item.unit,
                    reason=reason,
                    ref_no=ref_no,
                    notes=notes,
                    created_by=user
                )
                
                remaining_qty -= qty_from_selected
            
            # If still need more, consume from other lots using FEFO/FIFO
            if remaining_qty > 0:
                # Get other available lots (excluding the one we just used)
                consumption_plan = InventoryService.calculate_consumption_lots(item, remaining_qty)
                
                for next_lot, qty_to_consume in consumption_plan:
                    # Skip the lot we already consumed from
                    if next_lot.id == lot.id:
                        continue
                    
                    # Update lot quantity
                    next_lot.qty -= qty_to_consume
                    next_lot.save()
                    
                    # Create movement record
                    StockMovement.objects.create(
                        item=item,
                        lot=next_lot,
                        movement_type='consume',
                        qty=qty_to_consume,
                        unit=item.unit,
                        reason=reason,
                        ref_no=ref_no,
                        notes=f"{notes} (overflow from lot {lot.lot_no})" if notes else f"Overflow from lot {lot.lot_no}",
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
    def produce_stock(recipe, production_qty, lot_no, user, expires_at=None, notes=None, unit_cost=None):
        """
        Produce stock using recipe with optional unit cost
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
            qty_needed = Decimal(str(ingredient_data['qty']))
            
            available_stock = sum(lot.qty for lot in InventoryService.get_available_lots(ingredient))
            if available_stock < qty_needed:
                raise ValueError(f"Insufficient stock for {ingredient.name}. Need: {qty_needed}, Available: {available_stock}")
        
        # Consume ingredients
        for ingredient_data in required_ingredients:
            ingredient = ingredient_data['ingredient']
            qty_needed = Decimal(str(ingredient_data['qty']))
            
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
            unit_cost=unit_cost or 0,
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
        qty = Decimal(str(qty))
        
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


class PurchaseOrderService:
    """
    Service class for purchase order management
    """
    
    @staticmethod
    @transaction.atomic
    def create_purchase_order(supplier, items_data, user, notes=None, expected_delivery_date=None):
        """
        Create a new purchase order with multiple items
        items_data: list of dict with keys: item, qty, unit_price
        """
        # Create purchase order
        po = PurchaseOrder.objects.create(
            supplier=supplier,
            created_by=user,
            notes=notes,
            expected_delivery_date=expected_delivery_date,
            status='pending'
        )
        
        # Create order items
        total_amount = Decimal('0.00')
        for item_data in items_data:
            po_item = PurchaseOrderItem.objects.create(
                purchase_order=po,
                item=item_data['item'],
                qty_ordered=item_data['qty'],
                unit=item_data['item'].unit,
                unit_price=item_data.get('unit_price', 0),
                notes=item_data.get('notes', '')
            )
            total_amount += po_item.subtotal()
        
        # Update total amount
        po.total_amount = total_amount
        po.save()
        
        return po
    
    @staticmethod
    @transaction.atomic
    def supplier_approve_purchase_order(po, user, supplier_notes=None, expected_delivery_date=None):
        """
        Supplier approves purchase order with pricing
        """
        po.supplier_approve_order(user=user, supplier_notes=supplier_notes, expected_delivery_date=expected_delivery_date)
        return po
    
    @staticmethod
    @transaction.atomic
    def admin_approve_purchase_order(po, user, admin_notes=None):
        """
        Admin approves purchase order after reviewing pricing
        """
        po.admin_approve_order(user=user, admin_notes=admin_notes)
        return po
    
    @staticmethod
    @transaction.atomic
    def admin_reject_purchase_order(po, user, reason):
        """
        Admin rejects purchase order (price too high, etc.)
        """
        po.admin_reject_order(user=user, reason=reason)
        return po
    
    @staticmethod
    @transaction.atomic
    def cancel_purchase_order(po, user, reason):
        """
        Cancel purchase order with reason
        """
        po.cancel_order(user=user, reason=reason)
        return po
    
    @staticmethod
    @transaction.atomic
    def ship_purchase_order(po, user=None):
        """
        Mark purchase order as shipped
        """
        po.mark_shipped(user=user)
        return po
    
    @staticmethod
    @transaction.atomic
    def receive_purchase_order_by_qr(qr_code, user):
        """
        Receive purchase order by scanning QR code
        Automatically creates stock lots for all items in the order
        """
        try:
            po = PurchaseOrder.objects.get(qr_code=qr_code)
        except PurchaseOrder.DoesNotExist:
            raise ValueError("Invalid QR code. Purchase order not found.")
        
        if not po.can_be_received():
            raise ValueError(f"Purchase order cannot be received. Current status: {po.get_status_display()}")
        
        # Mark order as received
        po.mark_received(user)
        
        # Auto-receive all items as stock lots
        received_lots = []
        for po_item in po.order_items.all():
            # Generate lot number
            lot_no = f"{po.order_no}-{po_item.item.code}"
            
            # Calculate expiry date if item is perishable
            expires_at = None
            if po_item.item.is_perishable and po_item.item.shelf_life_days > 0:
                expires_at = timezone.now().date() + timedelta(days=po_item.item.shelf_life_days)
            
            # Create stock lot
            lot = InventoryService.receive_stock(
                item=po_item.item,
                lot_no=lot_no,
                qty=po_item.qty_ordered,
                unit=po_item.unit,
                user=user,
                supplier=po.supplier,
                expires_at=expires_at,
                unit_cost=po_item.unit_price,
                ref_no=po.order_no,
                notes=f"Received from PO: {po.order_no}"
            )
            
            # Update qty_received
            po_item.qty_received = po_item.qty_ordered
            po_item.save()
            
            received_lots.append(lot)
        
        return po, received_lots
    
    @staticmethod
    def generate_qr_code_image(qr_code):
        """
        Generate QR code image for a purchase order
        Returns base64 encoded image
        """
        import qrcode
        from io import BytesIO
        import base64
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def get_pending_orders():
        """
        Get all pending purchase orders
        """
        return PurchaseOrder.objects.filter(status='pending').order_by('-created_at')
    
    @staticmethod
    def get_shipped_orders():
        """
        Get all shipped purchase orders waiting to be received
        """
        return PurchaseOrder.objects.filter(status='shipped').order_by('-shipped_at')
    
    @staticmethod
    def get_order_summary():
        """
        Get purchase order summary statistics
        """
        return {
            'total_orders': PurchaseOrder.objects.count(),
            'pending_orders': PurchaseOrder.objects.filter(status='pending').count(),
            'approved_orders': PurchaseOrder.objects.filter(status='approved').count(),
            'shipped_orders': PurchaseOrder.objects.filter(status='shipped').count(),
            'received_orders': PurchaseOrder.objects.filter(status='received').count(),
        }
