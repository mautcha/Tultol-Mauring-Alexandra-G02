from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from dashboard.views import role_required
from .models import Mall, Floor, Store
from .forms import MallForm, FloorForm, StoreForm


# --- Shopper & Admin Directory Browsing ---

@login_required
def store_list_view(request):
    """Search and filter stores across malls, floors, and categories."""
    query = request.GET.get('q', '').strip()
    mall_id = request.GET.get('mall', '').strip()
    category = request.GET.get('category', '').strip()

    stores = Store.objects.select_related('mall', 'floor').all()
    if query:
        stores = stores.filter(
            Q(name__icontains=query)
            | Q(unit_code__icontains=query)
            | Q(landmark_directions__icontains=query)
        )
    if mall_id.isdigit():
        stores = stores.filter(mall_id=int(mall_id))
    if category:
        stores = stores.filter(category=category)

    malls = Mall.objects.all()
    is_admin = getattr(getattr(request.user, 'profile', None), 'role', 'shopper') == 'admin' or request.user.is_superuser

    return render(request, 'directory/store_list.html', {
        'stores': stores,
        'malls': malls,
        'categories': Store.CATEGORY_CHOICES,
        'query': query,
        'selected_mall': mall_id,
        'selected_category': category,
        'is_admin': is_admin,
    })


@login_required
def store_detail_view(request, pk):
    """Display full store location, floor info, and landmark directions."""
    store = get_object_or_404(Store.objects.select_related('mall', 'floor'), pk=pk)
    is_admin = getattr(getattr(request.user, 'profile', None), 'role', 'shopper') == 'admin' or request.user.is_superuser
    return render(request, 'directory/store_detail.html', {
        'store': store,
        'is_admin': is_admin,
    })


@login_required
def mall_list_view(request):
    """Browse all malls and their floor maps/levels."""
    malls = Mall.objects.prefetch_related('floors').all()
    is_admin = getattr(getattr(request.user, 'profile', None), 'role', 'shopper') == 'admin' or request.user.is_superuser
    return render(request, 'directory/mall_list.html', {
        'malls': malls,
        'is_admin': is_admin,
    })


# --- Mall Admin CRUD: Malls ---

@login_required
@role_required('admin')
def mall_create_view(request):
    """Allow Mall Admins to add a new mall."""
    if request.method == 'POST':
        form = MallForm(request.POST)
        if form.is_valid():
            mall = form.save(commit=False)
            mall.created_by = request.user
            mall.save()
            messages.success(request, f"Mall '{mall.name}' added successfully.")
            return redirect('directory:mall_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = MallForm()
    return render(request, 'directory/form.html', {
        'form': form,
        'title': 'Add Mall',
        'subtitle': 'Register a mall in Tultol.',
        'back_url': 'directory:mall_list',
    })


@login_required
@role_required('admin')
def mall_update_view(request, pk):
    """Allow Mall Admins to update a mall."""
    mall = get_object_or_404(Mall, pk=pk)
    if request.method == 'POST':
        form = MallForm(request.POST, instance=mall)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mall '{mall.name}' updated successfully.")
            return redirect('directory:mall_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = MallForm(instance=mall)
    return render(request, 'directory/form.html', {
        'form': form,
        'title': f'Edit Mall: {mall.name}',
        'subtitle': 'Update mall details and hours.',
        'back_url': 'directory:mall_list',
    })


@login_required
@role_required('admin')
@require_POST
def mall_delete_view(request, pk):
    """Allow Mall Admins to delete a mall."""
    mall = get_object_or_404(Mall, pk=pk)
    name = mall.name
    mall.delete()
    messages.success(request, f"Mall '{name}' deleted.")
    return redirect('directory:mall_list')


# --- Mall Admin CRUD: Floors ---

@login_required
@role_required('admin')
def floor_create_view(request):
    """Allow Mall Admins to add a floor to a mall."""
    if request.method == 'POST':
        form = FloorForm(request.POST)
        if form.is_valid():
            floor = form.save(commit=False)
            floor.created_by = request.user
            floor.save()
            messages.success(request, f"Floor '{floor.name}' added to {floor.mall.name}.")
            return redirect('directory:mall_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = FloorForm()
    return render(request, 'directory/form.html', {
        'form': form,
        'title': 'Add Floor Level',
        'subtitle': 'Add a navigable floor level to a mall.',
        'back_url': 'directory:mall_list',
    })


@login_required
@role_required('admin')
def floor_update_view(request, pk):
    """Allow Mall Admins to update a floor."""
    floor = get_object_or_404(Floor, pk=pk)
    if request.method == 'POST':
        form = FloorForm(request.POST, instance=floor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Floor '{floor.name}' updated.")
            return redirect('directory:mall_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = FloorForm(instance=floor)
    return render(request, 'directory/form.html', {
        'form': form,
        'title': f'Edit Floor: {floor.name}',
        'subtitle': f'Update floor details for {floor.mall.name}.',
        'back_url': 'directory:mall_list',
    })


@login_required
@role_required('admin')
@require_POST
def floor_delete_view(request, pk):
    """Allow Mall Admins to delete a floor."""
    floor = get_object_or_404(Floor, pk=pk)
    name = str(floor)
    floor.delete()
    messages.success(request, f"Floor '{name}' deleted.")
    return redirect('directory:mall_list')


# --- Mall Admin CRUD: Stores ---

@login_required
@role_required('admin')
def store_create_view(request):
    """Allow Mall Admins to add a store to the directory."""
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.mall = store.floor.mall
            store.created_by = request.user
            store.save()
            messages.success(request, f"Store '{store.name}' added to {store.mall.name}.")
            return redirect('directory:store_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = StoreForm()
    return render(request, 'directory/form.html', {
        'form': form,
        'title': 'Add Store / Tenant',
        'subtitle': 'Add a store with unit code and indoor directions.',
        'back_url': 'directory:store_list',
    })


@login_required
@role_required('admin')
def store_update_view(request, pk):
    """Allow Mall Admins to update a store."""
    store = get_object_or_404(Store, pk=pk)
    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, f"Store '{store.name}' updated.")
            return redirect('directory:store_detail', pk=store.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = StoreForm(instance=store)
    return render(request, 'directory/form.html', {
        'form': form,
        'title': f'Edit Store: {store.name}',
        'subtitle': 'Update unit location, directions, or status.',
        'back_url': 'directory:store_list',
    })


@login_required
@role_required('admin')
@require_POST
def store_delete_view(request, pk):
    """Allow Mall Admins to remove a store."""
    store = get_object_or_404(Store, pk=pk)
    name = store.name
    store.delete()
    messages.success(request, f"Store '{name}' deleted.")
    return redirect('directory:store_list')
