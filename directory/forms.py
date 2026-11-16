from django import forms
from django.core.exceptions import ValidationError
from .models import Mall, Floor, Store, SavedStore


class MallForm(forms.ModelForm):
    """Form for Mall Admins to create or update a mall."""

    class Meta:
        model = Mall
        fields = ['name', 'city', 'address', 'opening_hours']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. SM Seaside City Cebu'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Cebu City'}),
            'address': forms.TextInput(attrs={'placeholder': 'Street, Barangay, City'}),
            'opening_hours': forms.TextInput(attrs={'placeholder': 'e.g. 10:00 AM - 9:00 PM'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Mall.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A mall with this name already exists.")
        return name


class FloorForm(forms.ModelForm):
    """Form for Mall Admins to create or update a floor inside a mall."""

    class Meta:
        model = Floor
        fields = ['mall', 'floor_number', 'name', 'map_notes']
        widgets = {
            'floor_number': forms.NumberInput(attrs={'placeholder': '0 = Ground, 1 = 2nd Floor, -1 = Basement'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ground Floor'}),
            'map_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Key wings, entrances, or landmarks on this floor'}),
        }

    def clean(self):
        cleaned = super().clean()
        mall = cleaned.get('mall')
        floor_number = cleaned.get('floor_number')
        if mall is not None and floor_number is not None:
            qs = Floor.objects.filter(mall=mall, floor_number=floor_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('floor_number', f"Floor number {floor_number} already exists for {mall.name}.")
        return cleaned


class StoreForm(forms.ModelForm):
    """Form for Mall Admins to create or update a store on a specific mall floor."""

    class Meta:
        model = Store
        fields = ['floor', 'name', 'category', 'unit_code', 'landmark_directions', 'operating_hours', 'is_open']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. National Book Store'}),
            'unit_code': forms.TextInput(attrs={'placeholder': 'e.g. GF-104'}),
            'landmark_directions': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Near North Wing Entrance, across from Jollibee'}),
            'operating_hours': forms.TextInput(attrs={'placeholder': 'e.g. 10:00 AM - 9:00 PM'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['floor'].queryset = Floor.objects.select_related('mall').order_by('mall__name', 'floor_number')

    def clean_unit_code(self):
        return self.cleaned_data.get('unit_code', '').strip().upper()

    def clean(self):
        cleaned = super().clean()
        floor = cleaned.get('floor')
        unit_code = cleaned.get('unit_code')
        if floor and unit_code:
            qs = Store.objects.filter(floor=floor, unit_code__iexact=unit_code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('unit_code', f"Unit {unit_code} is already assigned on {floor}.")
        return cleaned

    def save(self, commit=True):
        store = super().save(commit=False)
        store.mall = store.floor.mall
        if commit:
            store.save()
        return store


class SavedStoreForm(forms.ModelForm):
    """Form for shoppers to add or update a personal note on a saved store."""

    class Meta:
        model = SavedStore
        fields = ['note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Optional note (e.g. Meet friends at 3 PM)'}),
        }
        labels = {
            'note': 'Personal Note',
        }

    def clean_note(self):
        return self.cleaned_data.get('note', '').strip()
