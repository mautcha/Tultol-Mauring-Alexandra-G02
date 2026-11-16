from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def role_required(role):
    """
    Decorator that checks if the logged-in user has the required role.
    If not, redirects them to their own dashboard with an error message.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            user_role = getattr(getattr(request.user, 'profile', None), 'role', 'shopper')
            if user_role != role and not (role == 'admin' and request.user.is_superuser):
                messages.error(request, "You do not have permission to access that page.")
                if user_role == 'admin' or request.user.is_superuser:
                    return redirect('dashboard:admin_dashboard')
                return redirect('dashboard:shopper_dashboard')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


@login_required
def home_view(request):
    """
    Generic dashboard redirect — sends users to their role-specific dashboard.
    """
    role = getattr(getattr(request.user, 'profile', None), 'role', 'shopper')
    if role == 'admin' or request.user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    return redirect('dashboard:shopper_dashboard')


@login_required
@role_required('shopper')
def shopper_dashboard(request):
    """
    Shopper (Mallgoer) Dashboard.
    Only accessible to users with the 'shopper' role.
    """
    return render(request, 'dashboard/shopper.html', {'user': request.user})


@login_required
@role_required('admin')
def admin_dashboard(request):
    """
    Mall Admin Dashboard.
    Only accessible to users with the 'admin' role or superusers.
    """
    from django.contrib.auth.models import User
    total_users = User.objects.count()
    total_shoppers = User.objects.filter(profile__role='shopper').count()
    total_admins = User.objects.filter(profile__role='admin').count()

    return render(request, 'dashboard/admin.html', {
        'user': request.user,
        'total_users': total_users,
        'total_shoppers': total_shoppers,
        'total_admins': total_admins,
    })
