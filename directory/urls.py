from django.urls import path
from . import views

app_name = 'directory'

urlpatterns = [
    path('', views.store_list_view, name='store_list'),
    path('stores/<int:pk>/', views.store_detail_view, name='store_detail'),
    path('stores/add/', views.store_create_view, name='store_create'),
    path('stores/<int:pk>/edit/', views.store_update_view, name='store_update'),
    path('stores/<int:pk>/delete/', views.store_delete_view, name='store_delete'),

    path('malls/', views.mall_list_view, name='mall_list'),
    path('malls/add/', views.mall_create_view, name='mall_create'),
    path('malls/<int:pk>/edit/', views.mall_update_view, name='mall_update'),
    path('malls/<int:pk>/delete/', views.mall_delete_view, name='mall_delete'),

    path('floors/add/', views.floor_create_view, name='floor_create'),
    path('floors/<int:pk>/edit/', views.floor_update_view, name='floor_update'),
    path('floors/<int:pk>/delete/', views.floor_delete_view, name='floor_delete'),

    path('saved/', views.saved_store_list_view, name='saved_list'),
    path('saved/add/<int:store_pk>/', views.saved_store_create_view, name='saved_create'),
    path('saved/<int:pk>/edit/', views.saved_store_update_view, name='saved_update'),
    path('saved/<int:pk>/delete/', views.saved_store_delete_view, name='saved_delete'),
]
