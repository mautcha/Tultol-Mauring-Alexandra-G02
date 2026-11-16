from django.contrib import admin
from .models import Mall, Floor, Store, SavedStore

admin.site.register(Mall)
admin.site.register(Floor)
admin.site.register(Store)
admin.site.register(SavedStore)
