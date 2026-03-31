from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
   
   path ('', views.login_view, name='login'),
   path  ('administrador/', include('panel_admin.urls')),
   path  ('empleado/', views.empleado_dashboard, name='empleado'),
   path ('personalizacion/', views.personalizacion, name='personalizacion'),
   path ('crear_personalizacion/', views.crear_personalizacion, name='crear_personalizacion'),
   path ('registrar_usuario/', views.registrar_usuario, name ='registrar_usuario'),
   path ('perfil/', views.cliente_perfil, name='perfil'),
   path  ('cliente/', views.cliente_dashboard, name='cliente'),
   path('<int:producto_id>/', views.agregar, name='agregar'),
   path('filtrar/', views.filtrar_producto, name='filtrar_producto'),
]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)