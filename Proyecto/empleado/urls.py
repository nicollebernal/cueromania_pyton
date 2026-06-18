from django.urls import path
from . import views

urlpatterns = [
    
    
    path('', views.empleado_dashboard, name='empleado'),
    path('inventario/', views.inventario_empleado, name='inventario_empleado'),
    path('ventas/', views.ventas_empleado, name='ventas_empleado'),
    path('pedidos-personalizados/', views.pedidos_personalizados, name='pedidos_personalizados'),
    path('cliente/', views.cliente_dashboard, name='empleado_cliente'),

   
    path('productos/', views.lista_productos, name='lista_productos'),
    path('agregar/<int:producto_id>/', views.agregar, name='agregar'),
    path('filtrar/', views.filtrar_producto, name='filtrar_producto'),

   
    path('editar/<int:producto_id>/', views.editar_producto_empleado, name='editar_producto_empleado'),
    path('sumar-stock/<int:producto_id>/', views.sumar_stock, name='sumar_stock'),
    path('restar-stock/<int:producto_id>/', views.restar_stock, name='restar_stock'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto_empleado, name='eliminar_producto_empleado'),
    
    # Nuevas rutas
    path('crear-producto/', views.crear_producto, name='crear_producto'),
    path('carrito-ventas/', views.carrito_ventas, name='carrito_ventas'),
    path('agregar-al-carrito/<int:producto_id>/', views.agregar_al_carrito_venta, name='agregar_al_carrito_venta'),
    path('quitar-del-carrito/<int:producto_id>/', views.quitar_del_carrito_venta, name='quitar_del_carrito_venta'),
    path('procesar-venta/', views.procesar_venta, name='procesar_venta'),
    path('factura/<int:venta_id>/', views.factura_venta, name='factura_venta'),
    path('factura-pdf/<int:venta_id>/', views.descargar_factura_pdf, name='descargar_factura_pdf'),
    
    path('guardar-personalizacion/', views.guardar_personalizacion, name='guardar_personalizacion'),
    path('editar-personalizacion/<int:personalizacion_id>/', views.editar_personalizacion, name='editar_personalizacion_empleado'),
    path('eliminar-personalizacion/<int:personalizacion_id>/', views.eliminar_personalizacion, name='eliminar_personalizacion'),
    path('cambiar-estado/<int:personalizacion_id>/', views.cambiar_estado_personalizacion, name='cambiar_estado_personalizacion'),
    # Ruta para importar productos desde CSV
    path('importar-productos/', views.importar_productos, name='importar_productos'),
]