from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, LoginForm, ProfileForm
from .models import Profile


def register_view(request):
    """
    Handles user registration with role selection, form validation, and password hashing.
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
    After logging in, redirects user directly to their role-specific dashboard.
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
                    user_match = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(request, username=user_match.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    user = None

            if user is not None:
                login(request, user)
                role_display = user.profile.get_role_display() if hasattr(user, 'profile') else 'User'
                messages.success(request, f"Welcome back, {user.username}! ({role_display})")
                
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                # Direct role-based redirection
                role = getattr(getattr(user, 'profile', None), 'role', 'shopper')
                if role == 'admin' or user.is_superuser:
                    return redirect('dashboard:admin_dashboard')
                return redirect('dashboard:shopper_dashboard')
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")
        else:
            messages.error(request, "Please enter both your username and password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    """
    Logs out the user and ends their session (POST only).
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Displays the logged-in user's own profile information.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
    })


@login_required
def profile_edit_view(request):
    """
    Allows the logged-in user to edit only their own profile details.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please fix the errors below and try again.")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def change_password_view(request):
    """
    Allows the logged-in user to change their own password without ending their session.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please fix the errors below and try again.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
