from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.login_view, name='login'),
    path('administrador/', views.admin_dashboard, name='administrador'),
    path('empleado/', views.empleado_dashboard, name='empleado'),
    path('empleado/inventario/', views.inventario_empleado, name='inventario_empleado'),
    path('empleado/ventas/', views.ventas_empleado, name='ventas_empleado'),
    path('empleado/pedidos-personalizados/', views.pedidos_personalizados, name='pedidos_personalizados'),
    path('cliente/', views.cliente_dashboard, name='cliente'),

   
    path('productos/', views.lista_productos, name='lista_productos'),
    path('agregar/<int:producto_id>/', views.agregar, name='agregar'),
    path('filtrar/', views.filtrar_producto, name='filtrar_producto'),

   
    path('empleado/editar/<int:producto_id>/', views.editar_producto_empleado, name='editar_producto_empleado'),
    path('empleado/sumar-stock/<int:producto_id>/', views.sumar_stock, name='sumar_stock'),
    path('empleado/restar-stock/<int:producto_id>/', views.restar_stock, name='restar_stock'),
    path('empleado/eliminar/<int:producto_id>/', views.eliminar_producto_empleado, name='eliminar_producto_empleado'),
]