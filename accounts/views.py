from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import RegistrationForm, LoginForm


def register_view(request):
    """
    Handles user registration with form validation and password hashing.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Welcome to Tultol, {user.username}! Your account has been created. Please log in."
            )
            return redirect('accounts:login')
        else:
            messages.error(
                request,
                "Please fix the errors below and try again."
            )
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handles user login. Authenticates using username or email.
    Shows error message when credentials are invalid.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            # Try authenticating directly with username
            user = authenticate(request, username=username_or_email, password=password)

            # If that fails, check if input was an email
            if user is None and '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    user = None

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard:home')
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")
        else:
            messages.error(request, "Please enter both your username and password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logs out the user and ends their session.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')
