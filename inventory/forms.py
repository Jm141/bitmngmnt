from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, UserAccess, UserLinks
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
