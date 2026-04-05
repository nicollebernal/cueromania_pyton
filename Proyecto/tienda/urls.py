from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
   
   path ('', views.login_view, name='login'),
   path ('logout/', views.logout_view, name='logout'),
   path ('recuperar/', views.password_reset_request, name='password_reset'),
   path ('recuperar/enviado/', views.password_reset_done, name='password_reset_done'),
   path ('cambiar-contraseña/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
   path ('recuperacion-completada/', views.password_reset_complete, name='password_reset_complete'),
   path  ('administrador/', include('panel_admin.urls')),
   path  ('empleado/', views.empleado_dashboard, name='empleado_tienda'),
   path ('personalizacion/', views.personalizacion, name='personalizacion'),
   path ('crear_personalizacion/', views.crear_personalizacion, name='crear_personalizacion'),
   path ('registrar_usuario/', views.registrar_usuario, name ='registrar_usuario'),
   path ('perfil/', views.cliente_perfil, name='perfil'),
   path  ('cliente/', views.cliente_dashboard, name='cliente'),
   path('valoraciones/', views.valoraciones, name='valoraciones'),
   path('valoraciones/crear/<int:producto_id>/', views.crear_valoracion, name='crear_valoracion'),
   path('<int:producto_id>/', views.agregar, name='agregar'),
   path('filtrar/', views.filtrar_producto, name='filtrar_producto'),
   path('nosotros/', views.nosotros, name='nosotros'),
   path('contacto/', views.contacto, name='contacto'), 
]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)