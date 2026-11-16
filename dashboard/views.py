from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    """
    Protected dashboard page. Only accessible to logged-in users.
    """
    return render(request, 'dashboard/home.html', {'user': request.user})
