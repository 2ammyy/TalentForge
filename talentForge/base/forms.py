from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
import re
from .models import UserProfile


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    # Field for delete profile picture
    remove_profile_picture = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Delete current profile picture"
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'website', 'profile_picture', 'profile_picture_url']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your location'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'profile_picture_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/photo.jpg'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for user fields
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean(self):
        cleaned_data = super().clean()
        profile_picture = cleaned_data.get('profile_picture')
        profile_picture_url = cleaned_data.get('profile_picture_url')
        remove_profile_picture = cleaned_data.get('remove_profile_picture')

        # Handle photo deletion
        if remove_profile_picture:
            # Clear both photo fields when deletion is requested
            cleaned_data['profile_picture'] = None
            cleaned_data['profile_picture_url'] = ''

        # Handle photo selection priority - uploaded file takes precedence over URL
        if profile_picture and profile_picture_url:
            # Clear the URL if a file is uploaded
            cleaned_data['profile_picture_url'] = ''

        # Validate URL if provided (basic validation)
        if profile_picture_url and not profile_picture:
            if not self.is_valid_image_url(profile_picture_url):
                raise forms.ValidationError({
                    'profile_picture_url': 'Please provide a valid URL to an image file (jpg, png, gif, etc.)'
                })

        return cleaned_data

    def is_valid_image_url(self, url):
        """Basic validation to check if URL points to an image"""
        if not url:
            return False
        image_patterns = [
            r'\.jpg$', r'\.jpeg$', r'\.png$', r'\.gif$', r'\.webp$', 
            r'\.bmp$', r'\.svg$', r'\.jfif$', r'\.ico$'
        ]
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in image_patterns)

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Update user information
        if self.instance.user:
            user = self.instance.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.email = self.cleaned_data.get('email', '')
            if commit:
                user.save()
        
        # Handle profile picture deletion
        remove_profile_picture = self.cleaned_data.get('remove_profile_picture')
        if remove_profile_picture:
            # Delete the uploaded file if it exists
            if instance.profile_picture:
                instance.profile_picture.delete(save=False)
                instance.profile_picture = None
            # Clear the URL
            instance.profile_picture_url = ''

        # Handle photo selection priority
        profile_picture = self.cleaned_data.get('profile_picture')
        profile_picture_url = self.cleaned_data.get('profile_picture_url')
        
        if profile_picture:
            instance.profile_picture_url = ''  # Clear URL when file is uploaded
        elif profile_picture_url:
            instance.profile_picture = None  # Clear file when URL is used

        if commit:
            instance.save()
        
        return instance


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Check if user exists
            user_exists = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).exists()
            
            if not user_exists:
                raise ValidationError("Account with this email/username does not exist.")
        
        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("There is no account registered with this email address.")
        return email


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )