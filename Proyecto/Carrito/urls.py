from django.urls import path
from . import views
urlpatterns = [
    path('', views.carro, name='carro'),
    path('agregar/<int:producto_id>/', views.agregar, name='agregar'),
    path('editar/<int:producto_id>/', views.editar, name='editar'),
    path('eliminar/<int:producto_id>/', views.eliminar, name='eliminar'),
    path('restar/<int:producto_id>/', views.restar, name='restar'),
    path('sumar/<int:producto_id>/', views.sumar, name='sumar'),  
    path('limpiar/', views.limpiar, name='limpiar'),
]