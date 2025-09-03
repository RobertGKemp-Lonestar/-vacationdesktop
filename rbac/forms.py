from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from .models import Role

# Use get_user_model() instead of direct import
User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'user_timezone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'user_timezone': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('UTC', 'UTC'),
                ('America/New_York', 'Eastern Time'),
                ('America/Chicago', 'Central Time'),
                ('America/Denver', 'Mountain Time'),
                ('America/Los_Angeles', 'Pacific Time'),
                ('America/Phoenix', 'Arizona Time'),
                ('America/Anchorage', 'Alaska Time'),
                ('Pacific/Honolulu', 'Hawaii Time'),
                ('Europe/London', 'London Time'),
                ('Europe/Paris', 'Paris Time'),
                ('Asia/Tokyo', 'Tokyo Time'),
                ('Australia/Sydney', 'Sydney Time'),
            ])
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'user_timezone':
                field.required = True


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        })


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    
    def get_users(self, email):
        """Return users with the given email address"""
        active_users = User._default_manager.filter(
            email__iexact=email,
            is_active=True,
        )
        return (u for u in active_users if u.has_usable_password())


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        })


# User Management Forms

class AddUserForm(forms.ModelForm):
    """Form for Client Admins to add users to their tenant"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'has_financial_access']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number (optional)'}),
            'has_financial_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        self.requesting_user = kwargs.pop('requesting_user', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on requesting user's permissions
        if self.requesting_user:
            if self.requesting_user.role.name == 'CLIENT_ADMIN':
                # Client admins can only assign CLIENT_USER role
                self.fields['role'].queryset = Role.objects.filter(name='CLIENT_USER')
            elif self.requesting_user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN']:
                # System admins can assign any role except SUPER_ADMIN
                self.fields['role'].queryset = Role.objects.exclude(name='SUPER_ADMIN')
            else:
                # Others can't create users
                self.fields['role'].queryset = Role.objects.none()
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already exists")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.tenant = self.tenant
        if commit:
            user.save()
        return user


class EditUserForm(forms.ModelForm):
    """Form for Client Admins to edit users in their tenant"""
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'phone', 'has_financial_access', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'has_financial_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.requesting_user = kwargs.pop('requesting_user', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on requesting user's permissions
        if self.requesting_user:
            if self.requesting_user.role.name == 'CLIENT_ADMIN':
                # Client admins can only assign CLIENT_USER role
                self.fields['role'].queryset = Role.objects.filter(name='CLIENT_USER')
            elif self.requesting_user.role.name in ['SUPER_ADMIN', 'SYSTEM_ADMIN']:
                # System admins can assign any role except SUPER_ADMIN
                self.fields['role'].queryset = Role.objects.exclude(name='SUPER_ADMIN')
            else:
                # Others can't edit users
                self.fields['role'].queryset = Role.objects.none()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email address already exists")
        return email


class ChangeUserPasswordForm(forms.Form):
    """Form for admins to change user passwords"""
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        help_text='Password must be at least 8 characters long.'
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self):
        if self.user:
            self.user.set_password(self.cleaned_data['new_password1'])
            self.user.save()
        return self.user