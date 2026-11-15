from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm


def register_view(request):
    """
    Handles user registration with form validation and password hashing.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Welcome to Tultol, {user.username}! Your account has been created successfully."
            )
            return redirect('accounts:register')
        else:
            messages.error(
                request,
                "Please fix the errors below and try again."
            )
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})
