from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Mall(models.Model):
    """Represents a Metro Cebu mall supported by Tultol."""

    name = models.CharField(max_length=120, unique=True)
    city = models.CharField(max_length=80, default='Cebu City')
    address = models.CharField(max_length=255)
    opening_hours = models.CharField(max_length=100, default='10:00 AM - 9:00 PM')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_malls'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"


class Floor(models.Model):
    """Represents a navigable level inside a mall."""

    mall = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField(help_text="Use -1 for Basement, 0 for Ground, 1 for 2nd Floor, etc.")
    name = models.CharField(max_length=80)
    map_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_floors'
    )

    class Meta:
        unique_together = ('mall', 'floor_number')
        ordering = ['mall__name', 'floor_number']

    def __str__(self):
        return f"{self.mall.name} — {self.name}"


class Store(models.Model):
    """Represents a store, restaurant, or facility located on a mall floor."""

    CATEGORY_CHOICES = [
        ('dining', 'Dining & Cafes'),
        ('fashion', 'Fashion & Apparel'),
        ('electronics', 'Electronics & Tech'),
        ('grocery', 'Grocery & Supermarket'),
        ('services', 'Services & Banks'),
        ('entertainment', 'Entertainment'),
        ('amenities', 'Restrooms / ATM / Exit'),
    ]

    mall = models.ForeignKey(Mall, on_delete=models.CASCADE, related_name='stores')
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='dining')
    unit_code = models.CharField(max_length=30)
    landmark_directions = models.TextField()
    operating_hours = models.CharField(max_length=100, default='10:00 AM - 9:00 PM')
    is_open = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_stores'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('floor', 'unit_code')
        ordering = ['name']

    def clean(self):
        if self.floor_id and self.mall_id and self.floor.mall_id != self.mall_id:
            raise ValidationError("Selected floor does not belong to the chosen mall.")

    def __str__(self):
        return f"{self.name} ({self.unit_code} - {self.floor.mall.name})"


class SavedStore(models.Model):
    """Represents a shopper's bookmarked store with a personal visit note."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_stores')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='saved_by_users')
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'store')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.store.name}"
