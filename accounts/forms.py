from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter a password'}),
        required=True
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Re-enter your password'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name (optional)'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['username'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Username is required.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as error:
                    self.add_error('password', error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash the password with Django's built-in authentication system
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Public registration always creates Shopper accounts
            user.profile.role = 'shopper'
            user.profile.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username or email'}),
        required=True
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        required=True
    )


class ProfileForm(forms.ModelForm):
    """Form for updating user profile info (name, email, contact number, photo)."""
    first_name = forms.CharField(
        label="First Name", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        label="Last Name", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        label="Email", required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )

    class Meta:
        model = Profile
        fields = ['contact_number', 'profile_photo']
        widgets = {
            'contact_number': forms.TextInput(attrs={'placeholder': 'e.g. 09171234567'}),
        }
        labels = {
            'contact_number': 'Contact Number',
            'profile_photo': 'Profile Photo',
        }

    def __init__(self, *args, **kwargs):
        # Accept the user instance so we can pre-fill user fields
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Allow same email (user is editing their own profile)
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("This email is already used by another account.")
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and hasattr(photo, 'size'):
            if photo.size > 2 * 1024 * 1024:
                raise ValidationError("Profile photo must be smaller than 2 MB.")
            content_type = getattr(photo, 'content_type', '')
            if content_type and not content_type.startswith('image/'):
                raise ValidationError("Please upload a valid image file.")
        return photo

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
