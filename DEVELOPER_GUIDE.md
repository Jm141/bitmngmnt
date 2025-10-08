# Bakery Inventory Management System - Developer Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Models Guide](#models-guide)
4. [Services Guide](#services-guide)
5. [Views Guide](#views-guide)
6. [Forms Guide](#forms-guide)
7. [Templates Guide](#templates-guide)
8. [Adding New Features](#adding-new-features)
9. [Modifying Existing Features](#modifying-existing-features)
10. [Database Operations](#database-operations)
11. [Testing Guidelines](#testing-guidelines)
12. [Deployment Notes](#deployment-notes)

## System Overview

The Bakery Inventory Management System is a Django-based application that manages inventory for bakery operations. It handles items, stock lots, movements, recipes, and production workflows with FEFO/FIFO logic.

### Key Features
- **Item Management**: CRUD operations for bakery items
- **Stock Tracking**: Lot-based inventory with expiry management
- **Recipe Management**: Production recipes with ingredient tracking
- **FEFO/FIFO Logic**: Smart stock consumption based on expiry dates
- **User Management**: Role-based access control
- **Audit Trail**: Complete activity logging

## Architecture

### Project Structure
```
bitmngmnt/
├── capstone/                 # Django project settings
├── inventory/                # Main app
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── forms.py             # Django forms
│   ├── services.py          # Business logic
│   ├── security.py          # Security utilities
│   ├── admin.py             # Django admin
│   ├── urls.py              # URL routing
│   ├── templates/           # HTML templates
│   └── migrations/          # Database migrations
├── manage.py
└── requirements.txt
```

### Design Patterns Used
- **Service Layer Pattern**: Business logic separated in `services.py`
- **Repository Pattern**: Model methods for data access
- **Decorator Pattern**: Security decorators for views
- **Factory Pattern**: Form generation and validation

## Models Guide

### Core Models

#### Item Model
```python
class Item(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2)
    is_perishable = models.BooleanField(default=False)
    shelf_life_days = models.PositiveIntegerField(default=0)
```

**Key Methods:**
- `get_current_stock()`: Calculate total available stock
- `is_low_stock()`: Check if below reorder level
- `get_expiring_soon(days)`: Get lots expiring within days

#### StockLot Model
```python
class StockLot(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    lot_no = models.CharField(max_length=100)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    expires_at = models.DateField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
```

**Key Methods:**
- `is_expired()`: Check if lot is expired
- `is_expiring_soon(days)`: Check if expiring within days

#### StockMovement Model
```python
class StockMovement(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.SET_NULL)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200)
```

**Key Methods:**
- `is_inbound()`: Check if movement increases stock
- `is_outbound()`: Check if movement decreases stock

### Adding New Models

1. **Define the model** in `models.py`:
```python
class NewModel(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'new_model'
        verbose_name = 'New Model'
```

2. **Create migration**:
```bash
python manage.py makemigrations inventory
python manage.py migrate
```

3. **Add to admin** in `admin.py`:
```python
@admin.register(NewModel)
class NewModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
```

## Services Guide

### InventoryService Class

The `InventoryService` class contains all business logic for inventory operations.

#### Key Methods

**Stock Consumption (FEFO/FIFO)**
```python
@staticmethod
def get_available_lots(item, qty_needed=None):
    """Get lots using FEFO for perishables, FIFO for non-perishables"""
    
@staticmethod
def consume_stock(item, qty, reason, user, lot=None):
    """Consume stock with automatic lot selection"""
```

**Stock Receiving**
```python
@staticmethod
def receive_stock(item, lot_no, qty, unit, user, **kwargs):
    """Receive new stock and create movement record"""
```

**Production**
```python
@staticmethod
def produce_stock(recipe, production_qty, lot_no, user, **kwargs):
    """Produce finished goods using recipe"""
```

### Adding New Service Methods

1. **Define the method** in `services.py`:
```python
@staticmethod
def new_operation(param1, param2, user):
    """Documentation for the new operation"""
    try:
        # Business logic here
        with transaction.atomic():
            # Database operations
            pass
        return result
    except Exception as e:
        raise ValueError(f"Error message: {str(e)}")
```

2. **Use in views**:
```python
def new_view(request):
    try:
        result = InventoryService.new_operation(param1, param2, request.user)
        messages.success(request, "Operation completed successfully")
    except Exception as e:
        messages.error(request, str(e))
```

## Views Guide

### View Structure

Views follow a consistent pattern:

```python
@login_required
@permission_required('inventory_read')  # or inventory_write
def view_name(request):
    """View documentation"""
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            try:
                # Business logic using services
                result = ServiceClass.operation(form.cleaned_data, request.user)
                
                # Log action
                log_user_action(
                    user=request.user,
                    action_type='create',  # or update, delete
                    target_model='ModelName',
                    target_id=result.id,
                    description="Action description",
                    request=request
                )
                
                messages.success(request, "Success message")
                return redirect('inventory:success_url')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = FormClass()
    
    context = {'form': form, 'title': 'Page Title'}
    return render(request, 'template.html', context)
```

### Adding New Views

1. **Create the view function** in `views.py`
2. **Add URL pattern** in `urls.py`:
```python
path('new-feature/', views.new_view, name='new_view'),
```
3. **Create template** in `templates/inventory/`
4. **Add navigation** in `base.html` if needed

## Forms Guide

### Form Structure

Forms follow Django best practices:

```python
class NewForm(forms.ModelForm):
    """Form documentation"""
    class Meta:
        model = ModelName
        fields = ['field1', 'field2']
        widgets = {
            'field1': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_field1(self):
        """Custom validation"""
        field1 = self.cleaned_data.get('field1')
        if field1:
            # Validation logic
            pass
        return field1
```

### Adding New Forms

1. **Define the form** in `forms.py`
2. **Add validation** in `clean_*` methods
3. **Use in views**:
```python
form = NewForm(request.POST)
if form.is_valid():
    instance = form.save(commit=False)
    instance.created_by = request.user
    instance.save()
```

## Templates Guide

### Template Structure

Templates extend `base.html` and follow Bootstrap styling:

```html
{% extends 'inventory/base.html' %}
{% load static %}

{% block title %}Page Title{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1 class="h3 mb-0">Page Title</h1>
        </div>
    </div>
    
    <div class="row">
        <div class="col-lg-8">
            <div class="card shadow">
                <div class="card-header py-3">
                    <h6 class="m-0 font-weight-bold text-primary">Section Title</h6>
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

### Adding New Templates

1. **Create template file** in `templates/inventory/`
2. **Follow naming convention**: `feature_name.html`
3. **Use consistent styling** with Bootstrap classes
4. **Include form handling** if applicable

## Adding New Features

### Step-by-Step Process

1. **Plan the Feature**
   - Define requirements
   - Identify affected models
   - Plan user interface

2. **Create/Modify Models**
   - Add new fields or models
   - Create migrations
   - Update admin interface

3. **Create Forms**
   - Define form classes
   - Add validation
   - Style with Bootstrap classes

4. **Implement Services**
   - Add business logic methods
   - Handle transactions
   - Add error handling

5. **Create Views**
   - Implement view functions
   - Add permission checks
   - Include audit logging

6. **Create Templates**
   - Design user interface
   - Handle form display
   - Add JavaScript if needed

7. **Add URL Patterns**
   - Define URL routes
   - Update navigation

8. **Test the Feature**
   - Test all scenarios
   - Verify permissions
   - Check error handling

### Example: Adding a New Feature

Let's add a "Stock Transfer" feature:

1. **Add to StockMovement model** (already exists):
```python
# Add to MOVEMENT_TYPES
('transfer', 'Transfer Stock'),
```

2. **Create service method**:
```python
@staticmethod
def transfer_stock(item, qty, from_location, to_location, user, **kwargs):
    """Transfer stock between locations"""
    # Implementation here
```

3. **Create form**:
```python
class StockTransferForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.filter(is_active=True))
    qty = forms.DecimalField(max_digits=10, decimal_places=2)
    from_location = forms.CharField(max_length=100)
    to_location = forms.CharField(max_length=100)
```

4. **Create view**:
```python
@login_required
@permission_required('inventory_write')
def stock_transfer(request):
    """Transfer stock between locations"""
    # Implementation here
```

5. **Create template**:
```html
<!-- stock_transfer.html -->
```

6. **Add URL**:
```python
path('stock/transfer/', views.stock_transfer, name='stock_transfer'),
```

## Modifying Existing Features

### Common Modifications

#### Adding New Fields to Models

1. **Modify model**:
```python
class Item(models.Model):
    # existing fields...
    new_field = models.CharField(max_length=100, blank=True)
```

2. **Create migration**:
```bash
python manage.py makemigrations inventory
python manage.py migrate
```

3. **Update forms**:
```python
class ItemForm(forms.ModelForm):
    class Meta:
        fields = ['code', 'name', 'new_field']  # Add new field
```

4. **Update templates**:
```html
<div class="form-group">
    <label for="{{ form.new_field.id_for_label }}">{{ form.new_field.label }}</label>
    {{ form.new_field }}
</div>
```

#### Modifying Business Logic

1. **Update service methods** in `services.py`
2. **Test thoroughly** with different scenarios
3. **Update documentation** if needed

#### Adding New Permissions

1. **Add to UserAccess.PERMISSION_TYPES**:
```python
PERMISSION_TYPES = [
    # existing permissions...
    ('new_permission', 'New Permission Description'),
]
```

2. **Use in views**:
```python
@permission_required('new_permission')
def new_view(request):
    pass
```

## Database Operations

### Query Patterns

#### Basic Queries
```python
# Get all active items
items = Item.objects.filter(is_active=True)

# Get items with low stock
low_stock_items = [item for item in Item.objects.filter(is_active=True) 
                   if item.is_low_stock()]

# Get recent movements
movements = StockMovement.objects.select_related('item', 'created_by').order_by('-timestamp')[:10]
```

#### Complex Queries
```python
# Get items with stock information
from django.db.models import Sum
items_with_stock = Item.objects.annotate(
    total_stock=Sum('stock_lots__qty')
).filter(is_active=True)

# Get expiring lots
from django.utils import timezone
from datetime import timedelta
expiry_date = timezone.now().date() + timedelta(days=7)
expiring_lots = StockLot.objects.filter(
    qty__gt=0,
    expires_at__lte=expiry_date,
    expires_at__isnull=False
)
```

### Performance Optimization

1. **Use select_related()** for foreign keys:
```python
movements = StockMovement.objects.select_related('item', 'lot', 'created_by')
```

2. **Use prefetch_related()** for many-to-many:
```python
recipes = Recipe.objects.prefetch_related('recipe_items__ingredient')
```

3. **Use database aggregation**:
```python
from django.db.models import Sum, Count
summary = Item.objects.aggregate(
    total_items=Count('id'),
    total_stock=Sum('stock_lots__qty')
)
```

## Testing Guidelines

### Unit Tests

Create tests in `tests.py`:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Item, StockLot
from .services import InventoryService

class InventoryServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.item = Item.objects.create(
            code='TEST001',
            name='Test Item',
            category='ingredient',
            unit='kg'
        )
    
    def test_consume_stock(self):
        # Create stock lot
        lot = StockLot.objects.create(
            item=self.item,
            lot_no='LOT001',
            qty=10,
            unit='kg'
        )
        
        # Consume stock
        InventoryService.consume_stock(
            item=self.item,
            qty=5,
            reason='Test consumption',
            user=self.user
        )
        
        # Verify
        lot.refresh_from_db()
        self.assertEqual(lot.qty, 5)
```

### Integration Tests

Test complete workflows:

```python
def test_production_workflow(self):
    # Create recipe
    recipe = Recipe.objects.create(
        name='Test Recipe',
        product=self.finished_item,
        yield_qty=10,
        yield_unit='pcs'
    )
    
    # Add ingredients
    RecipeItem.objects.create(
        recipe=recipe,
        ingredient=self.ingredient,
        qty=2,
        unit='kg'
    )
    
    # Create ingredient stock
    StockLot.objects.create(
        item=self.ingredient,
        lot_no='ING001',
        qty=5,
        unit='kg'
    )
    
    # Produce
    lot = InventoryService.produce_stock(
        recipe=recipe,
        production_qty=10,
        lot_no='PROD001',
        user=self.user
    )
    
    # Verify
    self.assertEqual(lot.qty, 10)
    self.assertEqual(lot.item, self.finished_item)
```

## Deployment Notes

### Environment Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure settings**:
```python
# In settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inventory_db',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. **Run migrations**:
```bash
python manage.py migrate
```

4. **Create superuser**:
```bash
python manage.py createsuperuser
```

### Production Considerations

1. **Static files**:
```bash
python manage.py collectstatic
```

2. **Database optimization**:
- Add database indexes for frequently queried fields
- Use connection pooling
- Monitor query performance

3. **Caching**:
```python
# Add Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

4. **Security**:
- Use HTTPS in production
- Set secure cookie settings
- Implement rate limiting
- Regular security updates

### Monitoring

1. **Logging**:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'inventory.log',
        },
    },
    'loggers': {
        'inventory': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

2. **Health checks**:
- Database connectivity
- Cache availability
- External service status

## Troubleshooting

### Common Issues

1. **Migration errors**:
```bash
# Reset migrations
python manage.py migrate inventory zero
python manage.py makemigrations inventory
python manage.py migrate
```

2. **Permission errors**:
- Check user permissions in admin
- Verify permission decorators in views
- Check UserAccess model records

3. **Stock calculation errors**:
- Verify FEFO/FIFO logic in services
- Check lot quantities and expiry dates
- Review transaction handling

### Debugging Tips

1. **Use Django shell**:
```bash
python manage.py shell
>>> from inventory.models import Item
>>> item = Item.objects.get(code='BREAD001')
>>> print(item.get_current_stock())
```

2. **Enable debug logging**:
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Debug message: {variable}")
```

3. **Use Django Debug Toolbar** in development

## Contributing

### Code Standards

1. **Follow PEP 8** for Python code
2. **Use meaningful variable names**
3. **Add docstrings** to all functions and classes
4. **Write tests** for new features
5. **Update documentation** when adding features

### Git Workflow

1. **Create feature branch**:
```bash
git checkout -b feature/new-feature
```

2. **Make changes** and commit:
```bash
git add .
git commit -m "Add new feature: description"
```

3. **Push and create PR**:
```bash
git push origin feature/new-feature
```

### Code Review Checklist

- [ ] Code follows project standards
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is proper

---

This developer guide provides comprehensive information for maintaining and extending the Bakery Inventory Management System. For specific questions or advanced scenarios, refer to Django documentation or create an issue in the project repository.
