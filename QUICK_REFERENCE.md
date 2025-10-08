# Quick Reference Guide - Bakery Inventory System

## 🚀 Quick Start Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Database Operations
```bash
# Create new migration
python manage.py makemigrations inventory

# Apply migrations
python manage.py migrate

# Reset migrations (if needed)
python manage.py migrate inventory zero
python manage.py makemigrations inventory
python manage.py migrate
```

## 📊 Model Quick Reference

### Item Model
```python
# Create item
item = Item.objects.create(
    code='BREAD001',
    name='White Bread',
    category='finished_good',
    unit='pcs',
    reorder_level=10,
    is_perishable=True,
    shelf_life_days=3
)

# Get current stock
stock = item.get_current_stock()

# Check if low stock
is_low = item.is_low_stock()

# Get expiring lots
expiring = item.get_expiring_soon(days=7)
```

### StockLot Model
```python
# Create stock lot
lot = StockLot.objects.create(
    item=item,
    lot_no='LOT001',
    qty=50,
    unit='pcs',
    expires_at=timezone.now().date() + timedelta(days=3),
    unit_cost=2.50
)

# Check expiry
is_expired = lot.is_expired()
is_expiring = lot.is_expiring_soon(days=7)
```

### StockMovement Model
```python
# Create movement
movement = StockMovement.objects.create(
    item=item,
    lot=lot,
    movement_type='receive',
    qty=50,
    unit='pcs',
    reason='Purchase from supplier',
    created_by=user
)

# Check movement type
is_inbound = movement.is_inbound()  # True for receive, produce, adjust
is_outbound = movement.is_outbound()  # True for consume, spoilage, transfer
```

## 🔧 Service Methods Quick Reference

### InventoryService Methods

#### Stock Operations
```python
# Receive stock
lot = InventoryService.receive_stock(
    item=item,
    lot_no='LOT001',
    qty=50,
    unit='pcs',
    user=user,
    supplier=supplier,
    expires_at=expiry_date,
    unit_cost=2.50
)

# Consume stock (auto FEFO/FIFO)
InventoryService.consume_stock(
    item=item,
    qty=10,
    reason='Production use',
    user=user
)

# Consume from specific lot
InventoryService.consume_stock(
    item=item,
    qty=10,
    reason='Production use',
    user=user,
    lot=specific_lot
)

# Adjust stock
InventoryService.adjust_stock(
    item=item,
    qty=5,  # Positive to increase, negative to decrease
    reason='Inventory count adjustment',
    user=user
)
```

#### Production Operations
```python
# Produce using recipe
produced_lot = InventoryService.produce_stock(
    recipe=recipe,
    production_qty=20,
    lot_no='PROD001',
    user=user,
    expires_at=expiry_date
)
```

#### Query Operations
```python
# Get available lots (FEFO/FIFO)
lots = InventoryService.get_available_lots(item, qty_needed=10)

# Calculate consumption plan
plan = InventoryService.calculate_consumption_lots(item, qty_needed=10)
# Returns: [(lot1, qty1), (lot2, qty2), ...]

# Get low stock items
low_stock = InventoryService.get_low_stock_items()
# Returns: [{'item': item, 'current_stock': 5, 'reorder_level': 10, 'shortage': 5}, ...]

# Get expiring items
expiring = InventoryService.get_expiring_items(days=7)

# Get expired items
expired = InventoryService.get_expired_items()

# Get stock summary
summary = InventoryService.get_stock_summary()
# Returns: {'total_items': 100, 'low_stock_count': 5, 'expiring_count': 3, 'expired_count': 1}

# Calculate item cost
cost = InventoryService.calculate_item_cost(item)
```

### RecipeService Methods

```python
# Calculate recipe cost
total_cost = RecipeService.calculate_recipe_cost(recipe)

# Validate production
validation = RecipeService.validate_recipe_production(recipe, production_qty=20)
# Returns: {'can_produce': True/False, 'missing_ingredients': [...], 'total_cost': 15.50}
```

## 🎯 View Patterns

### Standard CRUD View Pattern
```python
@login_required
@permission_required('inventory_read')
def item_list(request):
    """List items with search and filter"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    items = Item.objects.all()
    
    if search_query:
        items = items.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Add pagination
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)
    
    context = {
        'items': items,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    
    return render(request, 'inventory/item_list.html', context)
```

### Form Handling Pattern
```python
@login_required
@permission_required('inventory_write')
def item_create(request):
    """Create new item"""
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.created_by = request.user
                item.save()
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='Item',
                    target_id=item.id,
                    description=f"Created item {item.code}",
                    request=request
                )
                
                messages.success(request, f"Item {item.code} created successfully.")
                return redirect('inventory:item_detail', item_id=item.id)
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = ItemForm()
    
    context = {'form': form, 'title': 'Create Item'}
    return render(request, 'inventory/item_form.html', context)
```

### Service Integration Pattern
```python
@login_required
@permission_required('inventory_write')
def stock_receive(request):
    """Receive stock workflow"""
    if request.method == 'POST':
        form = StockReceiveForm(request.POST)
        if form.is_valid():
            try:
                lot = InventoryService.receive_stock(
                    item=form.cleaned_data['item'],
                    lot_no=form.cleaned_data['lot_no'],
                    qty=form.cleaned_data['qty'],
                    unit=form.cleaned_data['unit'],
                    user=request.user,
                    supplier=form.cleaned_data.get('supplier'),
                    expires_at=form.cleaned_data.get('expires_at'),
                    unit_cost=form.cleaned_data['unit_cost']
                )
                
                log_user_action(
                    user=request.user,
                    action_type='create',
                    target_model='StockLot',
                    target_id=lot.id,
                    description=f"Received stock: {lot.item.code}",
                    request=request
                )
                
                messages.success(request, f"Stock received successfully. Lot: {lot.lot_no}")
                return redirect('inventory:item_detail', item_id=lot.item.id)
                
            except Exception as e:
                messages.error(request, f"Error receiving stock: {str(e)}")
    else:
        form = StockReceiveForm()
    
    context = {'form': form, 'title': 'Receive Stock'}
    return render(request, 'inventory/stock_receive.html', context)
```

## 📝 Form Patterns

### ModelForm Pattern
```python
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['code', 'name', 'category', 'unit', 'reorder_level', 'is_perishable', 'shelf_life_days']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            if Item.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise ValidationError("An item with this code already exists.")
        return code
```

### Custom Form Pattern
```python
class StockReceiveForm(forms.Form):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    lot_no = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    qty = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty
```

## 🎨 Template Patterns

### Basic Template Structure
```html
{% extends 'inventory/base.html' %}
{% load static %}

{% block title %}Page Title{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h3 mb-0">Page Title</h1>
                <a href="{% url 'inventory:create_url' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Add New
                </a>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-lg-8">
            <div class="card shadow">
                <div class="card-header py-3">
                    <h6 class="m-0 font-weight-bold text-primary">Content Title</h6>
                </div>
                <div class="card-body">
                    <!-- Content here -->
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Form Template Pattern
```html
<form method="post">
    {% csrf_token %}
    
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label for="{{ form.field1.id_for_label }}">{{ form.field1.label }}</label>
                {{ form.field1 }}
                {% if form.field1.errors %}
                    <div class="text-danger">
                        {% for error in form.field1.errors %}
                            <small>{{ error }}</small>
                        {% endfor %}
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    {% if form.non_field_errors %}
        <div class="alert alert-danger">
            {% for error in form.non_field_errors %}
                {{ error }}
            {% endfor %}
        </div>
    {% endif %}
    
    <div class="form-group">
        <button type="submit" class="btn btn-primary">
            <i class="fas fa-save"></i> Save
        </button>
        <a href="{% url 'inventory:list_url' %}" class="btn btn-secondary">
            <i class="fas fa-times"></i> Cancel
        </a>
    </div>
</form>
```

### Table Template Pattern
```html
<div class="table-responsive">
    <table class="table table-bordered">
        <thead>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.field1 }}</td>
                <td>{{ item.field2 }}</td>
                <td>
                    <div class="btn-group" role="group">
                        <a href="{% url 'inventory:detail_url' item.id %}" 
                           class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="{% url 'inventory:update_url' item.id %}" 
                           class="btn btn-sm btn-outline-warning">
                            <i class="fas fa-edit"></i>
                        </a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

## 🔍 Common Queries

### Database Queries
```python
# Get items with current stock
from django.db.models import Sum
items_with_stock = Item.objects.annotate(
    current_stock=Sum('stock_lots__qty')
).filter(is_active=True)

# Get low stock items
low_stock_items = []
for item in Item.objects.filter(is_active=True):
    if item.is_low_stock():
        low_stock_items.append(item)

# Get recent movements
recent_movements = StockMovement.objects.select_related(
    'item', 'lot', 'created_by'
).order_by('-timestamp')[:10]

# Get expiring lots
from django.utils import timezone
from datetime import timedelta
expiry_date = timezone.now().date() + timedelta(days=7)
expiring_lots = StockLot.objects.filter(
    qty__gt=0,
    expires_at__lte=expiry_date,
    expires_at__isnull=False
).select_related('item')
```

## 🚨 Error Handling Patterns

### Service Error Handling
```python
@staticmethod
def consume_stock(item, qty, reason, user, lot=None):
    """Consume stock with error handling"""
    try:
        if lot:
            if lot.qty < qty:
                raise ValueError(f"Insufficient stock in lot. Available: {lot.qty}")
            lot.qty -= qty
            lot.save()
        else:
            consumption_plan = InventoryService.calculate_consumption_lots(item, qty)
            for lot, qty_to_consume in consumption_plan:
                lot.qty -= qty_to_consume
                lot.save()
        
        # Create movement record
        StockMovement.objects.create(
            item=item,
            lot=lot,
            movement_type='consume',
            qty=qty,
            unit=item.unit,
            reason=reason,
            created_by=user
        )
        
    except Exception as e:
        raise ValueError(f"Error consuming stock: {str(e)}")
```

### View Error Handling
```python
def stock_consume(request):
    if request.method == 'POST':
        form = StockConsumeForm(request.POST)
        if form.is_valid():
            try:
                InventoryService.consume_stock(
                    item=form.cleaned_data['item'],
                    qty=form.cleaned_data['qty'],
                    reason=form.cleaned_data['reason'],
                    user=request.user
                )
                messages.success(request, "Stock consumed successfully.")
                return redirect('inventory:item_detail', item_id=form.cleaned_data['item'].id)
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Unexpected error: {str(e)}")
```

## 🔐 Security Patterns

### Permission Decorators
```python
from .security import permission_required, admin_required, super_admin_required

@login_required
@permission_required('inventory_read')
def item_list(request):
    pass

@login_required
@permission_required('inventory_write')
def item_create(request):
    pass

@login_required
@admin_required
def admin_function(request):
    pass

@login_required
@super_admin_required
def super_admin_function(request):
    pass
```

### Audit Logging
```python
from .security import log_user_action

log_user_action(
    user=request.user,
    action_type='create',  # create, read, update, delete
    target_model='Item',
    target_id=item.id,
    description=f"Created item {item.code}",
    request=request
)
```

## 📊 Dashboard Data Patterns

### KPI Calculation
```python
def inventory_dashboard(request):
    # Get stock summary
    stock_summary = InventoryService.get_stock_summary()
    
    # Get low stock items
    low_stock_items = InventoryService.get_low_stock_items()
    
    # Get expiring items
    expiring_items = InventoryService.get_expiring_items(days=7)
    
    # Get recent movements
    recent_movements = StockMovement.objects.select_related(
        'item', 'created_by'
    ).order_by('-timestamp')[:10]
    
    context = {
        'stock_summary': stock_summary,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'recent_movements': recent_movements,
    }
    
    return render(request, 'inventory/inventory_dashboard.html', context)
```

---

This quick reference guide provides common patterns and examples for working with the Bakery Inventory Management System. Use it alongside the full Developer Guide for comprehensive development support.
