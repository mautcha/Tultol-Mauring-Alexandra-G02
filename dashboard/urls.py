from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('shopper/', views.shopper_dashboard, name='shopper_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
