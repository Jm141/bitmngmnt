from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import User, UserAccess, UserLinks, Supplier, Item, StockLot, StockMovement, Recipe, RecipeItem, PurchaseOrder, PurchaseOrderItem
from .security import validate_user_input, sanitize_input


class UserForm(forms.ModelForm):
    """
    Custom user form with additional fields and security
    """
    username = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'readonly': True, 'class': 'form-control'}))
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    birthday = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='staff')
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'birthday', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Handle username field
        if not self.instance.pk:
            # For new users, make username read-only and auto-generated
            self.fields['username'].widget.attrs.update({'readonly': True})
            self.fields['username'].help_text = "Username will be auto-generated from first and last name"
            self.fields['password1'].required = True
            self.fields['password2'].required = True
        else:
            # For existing users, keep username read-only
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = "Leave blank to keep current password"
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check for duplicate email
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A user with this email already exists.")
        return email
    
    def generate_username(self, first_name, last_name):
        """
        Generate username from first name and last name
        """
        # Create base username from first and last name
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        username = base_username
        
        # Check if username exists and add number if needed
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            phone_number = phone_number.strip()
            # Basic phone number validation
            if not phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
                raise ValidationError("Please enter a valid phone number.")
        return phone_number
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Generate username for new users
        if not self.instance.pk:  # Only for new users
            first_name = cleaned_data.get('first_name', '')
            last_name = cleaned_data.get('last_name', '')
            if first_name and last_name:
                generated_username = self.generate_username(first_name, last_name)
                cleaned_data['username'] = generated_username
                # Also set it in the form data for display
                self.data = self.data.copy()
                self.data['username'] = generated_username
        else:
            # For existing users, validate the username if provided
            username = cleaned_data.get('username')
            if username:
                username = username.lower().strip()
                if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("A user with this username already exists.")
                cleaned_data['username'] = username
        
        # Validate input for security
        is_valid, error_msg = validate_user_input(cleaned_data)
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Sanitize input
        cleaned_data = sanitize_input(cleaned_data)
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set username from cleaned data (already generated in clean method)
        username = self.cleaned_data.get('username')
        if not username:
            # Fallback: generate if somehow missing
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            username = self.generate_username(first_name, last_name) if first_name and last_name else None
        user.username = username or user.username
        
        # Set password for new users
        if not self.instance.pk:  # Only for new users
            user.set_password(self.cleaned_data['password1'])
        else:
            # For existing users, only set password if provided
            password = self.cleaned_data.get('password1')
            if password:
                user.set_password(password)
        
        # Set other fields
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.birthday = self.cleaned_data['birthday']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user information
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'birthday', 'role', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check for duplicate email
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower().strip()
            # Check for duplicate username
            if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A user with this username already exists.")
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate input for security
        is_valid, error_msg = validate_user_input(cleaned_data)
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Sanitize input
        cleaned_data = sanitize_input(cleaned_data)
        
        return cleaned_data


class UserAccessForm(forms.ModelForm):
    """
    Form for managing user permissions
    """
    class Meta:
        model = UserAccess
        fields = ('user', 'permission_type', 'expires_at')
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate input for security
        is_valid, error_msg = validate_user_input(cleaned_data)
        if not is_valid:
            raise ValidationError(error_msg)
        
        return cleaned_data


class UserLinksForm(forms.ModelForm):
    """
    Form for managing user relationships
    """
    class Meta:
        model = UserLinks
        fields = ('user', 'linked_user', 'link_type')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate input for security
        is_valid, error_msg = validate_user_input(cleaned_data)
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Check for self-linking
        user = cleaned_data.get('user')
        linked_user = cleaned_data.get('linked_user')
        
        if user and linked_user and user == linked_user:
            raise ValidationError("A user cannot be linked to themselves.")
        
        return cleaned_data


class UserSearchForm(forms.Form):
    """
    Form for searching users
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, name, or email...'
        })
    )
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + User.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_search(self):
        search_term = self.cleaned_data.get('search', '')
        if search_term:
            search_term = search_term.strip()
            # Validate search term for security
            is_valid, error_msg = validate_user_input({'search': search_term})
            if not is_valid:
                raise ValidationError(error_msg)
        return search_term


class PasswordChangeForm(forms.Form):
    """
    Form for changing user password
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("New passwords don't match.")
            
            # Validate password strength
            if len(new_password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user


# --- INVENTORY FORMS ---

class SupplierForm(forms.ModelForm):
    """
    Form for managing suppliers with optional user account creation
    """
    # Optional user account fields
    create_user_account = forms.BooleanField(
        required=False,
        initial=False,
        label="Create User Account for Supplier Portal",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Check this to create a login account for this supplier to access the supplier portal"
    )
    user_first_name = forms.CharField(
        max_length=30,
        required=False,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Required if creating user account'})
    )
    user_last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Required if creating user account'})
    )
    user_password = forms.CharField(
        required=False,
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Required if creating user account'}),
        help_text="Password for supplier login"
    )
    user_password_confirm = forms.CharField(
        required=False,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            # Check for duplicate name
            if Supplier.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A supplier with this name already exists.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check for duplicate email
            if Supplier.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A supplier with this email already exists.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        create_account = cleaned_data.get('create_user_account')
        
        if create_account:
            # Validate required fields for user account
            first_name = cleaned_data.get('user_first_name')
            last_name = cleaned_data.get('user_last_name')
            password = cleaned_data.get('user_password')
            password_confirm = cleaned_data.get('user_password_confirm')
            email = cleaned_data.get('email')
            
            if not first_name:
                raise ValidationError("First name is required when creating a user account.")
            if not last_name:
                raise ValidationError("Last name is required when creating a user account.")
            if not password:
                raise ValidationError("Password is required when creating a user account.")
            if not password_confirm:
                raise ValidationError("Password confirmation is required when creating a user account.")
            if password != password_confirm:
                raise ValidationError("Passwords do not match.")
            if not email:
                raise ValidationError("Email is required when creating a user account.")
            
            # Check if email is already used by another user
            if User.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
        
        return cleaned_data


class ItemForm(forms.ModelForm):
    """
    Form for managing items (code is auto-generated)
    """
    class Meta:
        model = Item
        fields = ['name', 'category', 'unit', 'description', 'reorder_level', 'min_order_qty', 'is_perishable', 'shelf_life_days', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_order_qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_perishable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shelf_life_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # Check for duplicate code
            if Item.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise ValidationError("An item with this code already exists.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        is_perishable = cleaned_data.get('is_perishable')
        shelf_life_days = cleaned_data.get('shelf_life_days')

        if is_perishable and shelf_life_days == 0:
            raise ValidationError("Shelf life days must be greater than 0 for perishable items.")

        return cleaned_data


class StockLotForm(forms.ModelForm):
    """
    Form for managing stock lots
    """
    class Meta:
        model = StockLot
        fields = ['item', 'lot_no', 'qty', 'unit', 'expires_at', 'unit_cost', 'supplier', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'lot_no': forms.TextInput(attrs={'class': 'form-control'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'expires_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter items to only show active ones
        self.fields['item'].queryset = Item.objects.filter(is_active=True)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost is not None and unit_cost < 0:
            raise ValidationError("Unit cost cannot be negative.")
        return unit_cost


class StockMovementForm(forms.ModelForm):
    """
    Form for managing stock movements
    """
    class Meta:
        model = StockMovement
        fields = ['item', 'lot', 'movement_type', 'qty', 'unit', 'ref_no', 'reason', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'lot': forms.Select(attrs={'class': 'form-control'}),
            'movement_type': forms.Select(attrs={'class': 'form-control'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'ref_no': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter items to only show active ones
        self.fields['item'].queryset = Item.objects.filter(is_active=True)
        # Filter lots to only show those with quantity > 0
        self.fields['lot'].queryset = StockLot.objects.filter(qty__gt=0)

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        lot = cleaned_data.get('lot')
        qty = cleaned_data.get('qty')

        # For outbound movements, check if lot has enough quantity
        if movement_type in ['consume', 'spoilage', 'transfer'] and lot and qty:
            if qty > lot.qty:
                raise ValidationError(f"Insufficient stock. Available: {lot.qty} {lot.unit}")

        return cleaned_data


class RecipeForm(forms.ModelForm):
    """
    Form for managing recipes
    """
    class Meta:
        model = Recipe
        fields = ['name', 'product', 'yield_qty', 'yield_unit', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'yield_qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'yield_unit': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter products to only show finished goods
        self.fields['product'].queryset = Item.objects.filter(category='finished_good', is_active=True)

    def clean_yield_qty(self):
        yield_qty = self.cleaned_data.get('yield_qty')
        if yield_qty is not None and yield_qty <= 0:
            raise ValidationError("Yield quantity must be greater than 0.")
        return yield_qty


class RecipeItemForm(forms.ModelForm):
    """
    Form for managing recipe items
    """
    class Meta:
        model = RecipeItem
        fields = ['ingredient', 'qty', 'unit', 'loss_factor', 'notes']
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-control'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'loss_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter ingredients to only show active ones
        self.fields['ingredient'].queryset = Item.objects.filter(category='ingredient', is_active=True)

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty

    def clean_loss_factor(self):
        loss_factor = self.cleaned_data.get('loss_factor')
        if loss_factor is not None and (loss_factor < 0 or loss_factor > 100):
            raise ValidationError("Loss factor must be between 0 and 100.")
        return loss_factor


class StockReceiveForm(forms.Form):
    """
    Form for receiving stock (lot_no is auto-generated if not provided)
    """
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    lot_no = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if left blank'})
    )
    qty = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    unit = forms.ChoiceField(
        choices=Item.UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    expires_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    unit_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    ref_no = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost is not None and unit_cost < 0:
            raise ValidationError("Unit cost cannot be negative.")
        return unit_cost


class StockConsumeForm(forms.Form):
    """
    Form for consuming stock
    """
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    lot = forms.ModelChoiceField(
        queryset=StockLot.objects.filter(qty__gt=0),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    qty = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    unit = forms.ChoiceField(
        choices=Item.UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ref_no = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty


class ProductionForm(forms.Form):
    """
    Form for production workflow
    """
    recipe = forms.ModelChoiceField(
        queryset=Recipe.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    production_qty = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    lot_no = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    expires_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean_production_qty(self):
        production_qty = self.cleaned_data.get('production_qty')
        if production_qty is not None and production_qty <= 0:
            raise ValidationError("Production quantity must be greater than 0.")
        return production_qty


# --- PURCHASE ORDER FORMS ---

class PurchaseOrderForm(forms.ModelForm):
    """
    Form for creating purchase orders (staff creates, supplier sets prices later)
    """
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Special instructions or requirements...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter suppliers to only show active ones
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['notes'].help_text = "Any special requirements or delivery instructions"


class PurchaseOrderItemForm(forms.ModelForm):
    """
    Form for adding items to purchase order
    """
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'qty_ordered', 'unit_price', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'qty_ordered': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter items to only show active ingredients
        self.fields['item'].queryset = Item.objects.filter(is_active=True)

    def clean_qty_ordered(self):
        qty = self.cleaned_data.get('qty_ordered')
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return qty

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price < 0:
            raise ValidationError("Unit price cannot be negative.")
        return price


class PurchaseOrderApproveForm(forms.Form):
    """
    Form for supplier to approve purchase order with pricing
    Supplier fills in unit prices and delivery date during approval
    """
    expected_delivery_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="When can you deliver this order?"
    )
    supplier_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any notes or special conditions...'}),
        help_text="Any notes, conditions, or comments about this order"
    )

    def __init__(self, *args, **kwargs):
        self.order_items = kwargs.pop('order_items', None)
        super().__init__(*args, **kwargs)
        
        # Dynamically add price fields for each order item
        if self.order_items:
            for idx, po_item in enumerate(self.order_items):
                field_name = f'item_price_{po_item.id}'
                self.fields[field_name] = forms.DecimalField(
                    label=f'Unit Price for {po_item.item.name}',
                    max_digits=10,
                    decimal_places=2,
                    required=True,
                    initial=po_item.unit_price if po_item.unit_price > 0 else None,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': '0.01',
                        'min': '0.01',
                        'placeholder': f'Price per {po_item.get_unit_display()}'
                    }),
                    help_text=f'Quantity: {po_item.qty_ordered} {po_item.get_unit_display()}'
                )

    def clean_expected_delivery_date(self):
        date = self.cleaned_data.get('expected_delivery_date')
        if date and date < timezone.now().date():
            raise ValidationError("Expected delivery date cannot be in the past.")
        return date
    
    def get_item_prices(self):
        """Extract item prices from cleaned data"""
        prices = {}
        for key, value in self.cleaned_data.items():
            if key.startswith('item_price_'):
                item_id = key.replace('item_price_', '')
                prices[item_id] = value
        return prices


class QRCodeScanForm(forms.Form):
    """
    Form for scanning QR code to receive purchase order
    """
    qr_code = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan or enter QR code...',
            'autofocus': True
        }),
        help_text="Scan the QR code from the delivery package or enter manually"
    )

    def clean_qr_code(self):
        qr_code = self.cleaned_data.get('qr_code')
        if qr_code:
            qr_code = qr_code.strip().upper()
            # Verify QR code format
            if not qr_code.startswith('PO-'):
                raise ValidationError("Invalid QR code format. QR code must start with 'PO-'")
        return qr_code
