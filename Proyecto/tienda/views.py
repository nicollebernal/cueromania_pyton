from datetime import date, timedelta, datetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.db.models import Avg, OuterRef, Subquery, Max
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import hashlib
import secrets
import logging
from .models import (
    Usuario, Producto, Rol, Personalizacion, 
    Valoracion, Venta, DetalleVenta, 
    categoria, colores, marcas, genero,
)
from Carrito.carro import Carro



def login_view(request):
    if request.method == 'POST':
        request.session.flush()
        
        gmail = request.POST.get('gmail', '').strip()
        clave = request.POST.get('clave', '')

        usuario = Usuario.objects.filter(gmail__iexact=gmail).select_related('id_rol').first()

        if not usuario:
            return render(request, 'login/login.html', {'error': 'Usuario no encontrado'})

        if not usuario.verificar_clave(clave):
            return render(request, 'login/login.html', {'error': 'Contraseña incorrecta'})

        usuario.migrar_clave_a_hash_django(clave)
        request.session['usuario_id'] = usuario.id_usuario

        rol_nombre = (usuario.id_rol.nombre_rol or '').strip().lower() if usuario.id_rol else ''
        if rol_nombre == 'administrador':
            return redirect('administrador')
        if rol_nombre == 'empleado':
            return redirect('empleado')
        if rol_nombre == 'cliente':
            return redirect('cliente')
        return render(request, 'login/login.html', {'error': 'Rol no válido'})

    return render(request, 'login/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('/')

def registrar_usuario(request):
    request.session.flush()
    if request.method == 'POST':
        id_usuario = request.POST['id_usuario']
        clave = make_password(request.POST['clave'])
        rol_cliente = Rol.objects.get(nombre_rol__iexact='cliente')


        usuario = Usuario.objects.create(
            id_usuario=id_usuario,
            primer_nombre=request.POST['primer_nombre'],
            segundo_nombre=request.POST['segundo_nombre'],
            primer_apellido=request.POST['primer_apellido'],
            segundo_apellido=request.POST['segundo_apellido'],
            direccion=request.POST['direccion'],
            contacto=request.POST['contacto'],
            gmail=request.POST['gmail'],
            clave=clave,
            id_rol=rol_cliente
        )
        usuario.save()
        request.session.flush()

        return redirect('login')

    roles = Rol.objects.all()
    return render(request, 'login/registro.html', {'roles': roles})



def cliente_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    mensaje = ''
    if request.method == 'POST':
        usuario.primer_nombre = request.POST.get('primer_nombre', usuario.primer_nombre).strip()
        usuario.primer_apellido = request.POST.get('primer_apellido', usuario.primer_apellido).strip()
        usuario.direccion = request.POST.get('direccion', usuario.direccion).strip()
        usuario.contacto = request.POST.get('contacto', usuario.contacto).strip()
        usuario.gmail = request.POST.get('gmail', usuario.gmail).strip()
        usuario.save()
        mensaje = 'Perfil actualizado correctamente.'
    return render(request, 'cliente/perfil.html', {'usuario': usuario, 'mensaje': mensaje})


def empleado_dashboard(request):
    return render(request, 'Empleado/empleado.html')

from django.db.models import Avg

def cliente_dashboard(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    productos = Producto.objects.annotate(avg_rating=Avg('valoraciones__valor_puntuacion')).all()
    carro = Carro(request)
    for producto in productos:
        producto.cantidad_en_carro = carro.carro.get(str(producto.id_producto), {}).get('cantidad', 0)
    return render(request, 'cliente/cliente.html', {'usuario': usuario, 'productos': productos})

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'cliente/cliente.html', {'productos': productos})

def agregar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    carro.agregar(producto)
    return redirect('cliente')

def filtrar_producto(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(nombre__icontains=query).annotate(avg_rating=Avg('valoraciones__valor_puntuacion')) if query else Producto.objects.annotate(avg_rating=Avg('valoraciones__valor_puntuacion')).all()
    carro = Carro(request)
    for producto in productos:
        producto.cantidad_en_carro = carro.carro.get(str(producto.id_producto), {}).get('cantidad', 0)
    return render(request, 'cliente/cliente.html', {'usuario': usuario, 'productos': productos, 'query': query})



def personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    personalizaciones = Personalizacion.objects.filter(id_usuario=usuario).annotate(
        categoria_nombre=Subquery(
            categoria.objects.filter(pk=OuterRef('id_categoria')).values('nombre_categoria')[:1]
        ),
        color_nombre=Subquery(
            colores.objects.filter(pk=OuterRef('id_color')).values('nombre_color')[:1]
        ),
        marca_nombre=Subquery(
            marcas.objects.filter(pk=OuterRef('id_marca')).values('nombre_marca')[:1]
        ),
        genero_nombre=Subquery(
            genero.objects.filter(pk=OuterRef('id_genero')).values('nombre_genero')[:1]
        ),
    )
    return render(request, 'cliente/personalizacion.html', {
        'usuario': usuario,
        'personalizaciones': personalizaciones,
        'categorias': categoria.objects.all(),
        'colores': colores.objects.all(),
        'marcas': marcas.objects.all(),
        'generos': genero.objects.all(),
    })
    
    

def crear_personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        fecha_solicitud_raw = request.POST.get('fecha_solicitud', '').strip()
        id_categoria = request.POST.get('id_categoria')
        id_color = request.POST.get('id_color')
        id_marca = request.POST.get('id_marca')
        id_genero = request.POST.get('id_genero')

        if not descripcion or not id_categoria or not id_color or not id_marca or not id_genero:
            messages.error(request, 'Completa todos los campos obligatorios para enviar la propuesta.')
            return redirect('personalizacion')

        try:
            if fecha_solicitud_raw:
                fecha_solicitud = date.fromisoformat(fecha_solicitud_raw)
            else:
                fecha_solicitud = date.today()

            next_id = Personalizacion.objects.aggregate(max_id=Max('id_personalizacion'))['max_id'] or 0
            next_id = max(next_id, 0) + 1

            Personalizacion.objects.create(
                id_personalizacion=next_id,
                id_usuario_id=usuario_id,
                descripcion=descripcion,
                fecha_solicitud=fecha_solicitud,
                id_categoria_id=id_categoria,
                id_color_id=id_color,
                id_marca_id=id_marca,
                id_genero_id=id_genero,
                imagen_personalizacion=request.FILES.get('imagen_personalizacion')
            )
            messages.success(request, 'Propuesta de diseño enviada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al enviar propuesta de diseño: {str(e)}')

    return redirect('personalizacion')

def valoraciones(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    reviews = Valoracion.objects.filter(id_usuario=usuario).select_related('id_producto')
    reviewed_ids = set(reviews.values_list('id_producto_id', flat=True))
    compras = DetalleVenta.objects.filter(id_venta__id_usuario=usuario).select_related('id_producto', 'id_venta')
    productos_pendientes = [d for d in compras if d.id_producto.id_producto not in reviewed_ids]
    return render(request, 'cliente/valoraciones.html', {
        'usuario': usuario, 'reviews': reviews, 'productos_pendientes': productos_pendientes
    })

def crear_valoracion(request, producto_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    producto = get_object_or_404(Producto, id_producto=producto_id)

    if request.method == 'POST':
        valor = request.POST.get('valor_puntuacion')
        comentario = request.POST.get('comentario', '').strip()
        # Capturamos la foto que viene del formulario
        foto = request.FILES.get('foto_valoracion') 

        if valor:
            # Creamos la valoración en la base de datos
            Valoracion.objects.create(
                valor_puntuacion=int(valor),
                comentario=comentario,
                id_usuario=usuario,
                id_producto=producto,
                imagen_valoracion=foto,
                fecha_puntuacion=date.today()
            )
            messages.success(request, '¡Gracias por tu valoración!')
            return redirect('valoraciones')
        else:
            messages.error(request, 'Debes seleccionar una puntuación.')

    return render(request, 'cliente/crear_valoracion.html', {'producto': producto})

def nosotros(request):
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        usuario = Usuario.objects.get(id_usuario=usuario_id)
        return render(request, 'cliente/nosotros.html', {'usuario': usuario})
    return render(request, 'cliente/nosotros.html')
def contacto(request):
    return render(request, 'tienda/contacto.html')



def password_reset_request(request):
    """Solicita recuperación de contraseña por email."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            usuario = Usuario.objects.get(gmail__iexact=email)
        except Usuario.DoesNotExist:
           
            messages.success(request, 'Si el email existe en nuestros registros, recibirás un enlace para recuperar tu contraseña.')
            return redirect('password_reset_done')
        
       
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
       
        timestamp_24h = int(datetime.now().timestamp() / 86400) * 86400
        token = hashlib.sha256(f'{usuario.id_usuario}|{usuario.clave}|{timestamp_24h}'.encode()).hexdigest()
        
       
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        reset_url = f'{protocol}://{domain}/cambiar-contraseña/{uid}/{token}/'
        
        
        subject = 'Recupera tu contraseña - Cueromanía'
        logo_url = f'{protocol}://{domain}/static/img/logo.jpeg'
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                    
                    <!-- Header con logo -->
                    <div style="background: linear-gradient(135deg, #5a0f14 0%, #8b1c24 100%); padding: 30px; text-align: center;">
                        <img src="{logo_url}" alt="Cueromanía" style="max-width: 150px; height: auto; margin-bottom: 15px; border-radius: 8px;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Cueromanía</h1>
                    </div>
                    
                    <!-- Contenido -->
                    <div style="padding: 40px;">
                        <h2 style="color: #5a0f14; margin-top: 0;">¡Hola {usuario.primer_nombre}!</h2>
                        <p style="color: #333; font-size: 16px; line-height: 1.6;">
                            Recibimos una solicitud para recuperar tu contraseña en <strong>Cueromanía</strong>.
                        </p>
                        
                        <p style="color: #333; font-size: 16px; line-height: 1.6;">
                            Haz clic en el botón de abajo para crear una nueva contraseña:
                        </p>
                        
                        <!-- Botón -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="background-color: #8b1c24; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                                Recuperar Contraseña
                            </a>
                        </div>
                        
                        <!-- Información adicional -->
                        <p style="color: #999; font-size: 13px; line-height: 1.6;">
                            Si el botón anterior no funciona, copia y pega este enlace en tu navegador:<br>
                            <a href="{reset_url}" style="color: #8b1c24; text-decoration: none; word-break: break-all;">{reset_url}</a>
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #666; font-size: 14px; line-height: 1.6;">
                            ⏰ <strong>Este enlace expira en 24 horas</strong>
                        </p>
                        
                        <p style="color: #666; font-size: 14px;">
                            Si no solicitaste recuperar tu contraseña, puedes ignorar este email de forma segura.
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                        <p style="color: #999; font-size: 12px; margin: 0;">
                            <strong>Cueromanía S.A.S.</strong><br>
                            Somos expertos en cuero de calidad premium
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 10px 0 0 0;">
                            © 2026 Cueromanía. Todos los derechos reservados.
                        </p>
                    </div>
                    
                </div>
            </body>
        </html>
        """
        
        # Mensaje de texto plano como fallback
        text_message = f"""
Hola {usuario.primer_nombre},

Recibimos una solicitud para recuperar tu contraseña en Cueromanía.
Haz clic en el siguiente enlace para crear una nueva contraseña:

{reset_url}

Este enlace expira en 24 horas.

Si no solicitaste esto, ignora este email.

Saludos,
Equipo de Cueromanía
"""
        
        try:
            from django.core.mail import EmailMultiAlternatives
            msg = EmailMultiAlternatives(
                subject,
                text_message,
                'Cueromanía <' + settings.DEFAULT_FROM_EMAIL + '>',
                [usuario.gmail]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
            print(f"[DEBUG] Email enviado exitosamente a {usuario.gmail}")
            messages.success(request, 'Si el email existe en nuestros registros, recibirás un enlace para recuperar tu contraseña.')
            return redirect('password_reset_done')
        except Exception as e:
            
            logger = logging.getLogger(__name__)
            logger.error('Password reset email sending failed')
            print(f"[DEBUG] Error enviando email: {str(e)}")
            # Mismo mensaje de éxito para no revelar información
            messages.success(request, 'Si el email existe en nuestros registros, recibirás un enlace para recuperar tu contraseña.')
            return redirect('password_reset_done')
    
    return render(request, 'login/password_reset_email.html')


def password_reset_done(request):
    """Confirma que el email fue enviado."""
    return render(request, 'login/password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """Confirma el token y permite cambiar la contraseña."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None
    
    
    is_valid_token = False
    if usuario is not None:
       
        timestamp_24h = int(datetime.now().timestamp() / 86400) * 86400
        expected_token = hashlib.sha256(f'{usuario.id_usuario}|{usuario.clave}|{timestamp_24h}'.encode()).hexdigest()
        
        
        timestamp_24h_prev = timestamp_24h - 86400
        expected_token_prev = hashlib.sha256(f'{usuario.id_usuario}|{usuario.clave}|{timestamp_24h_prev}'.encode()).hexdigest()
        
        if token == expected_token or token == expected_token_prev:
            is_valid_token = True
    
    if usuario is None or not is_valid_token:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('login')
    
    if request.method == 'POST':
        clave_vieja = request.POST.get('clave_vieja', '').strip()
        clave_nueva = request.POST.get('clave_nueva', '').strip()
        clave_confirmar = request.POST.get('clave_confirmar', '').strip()
        
        # Validar contraseña vieja
        if not clave_vieja:
            messages.error(request, 'Debes ingresar tu contraseña actual.')
            return render(request, 'login/password_reset_confirm.html', {
                'uidb64': uidb64, 
                'token': token,
                'usuario': usuario
            })
        
        if not usuario.verificar_clave(clave_vieja):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return render(request, 'login/password_reset_confirm.html', {
                'uidb64': uidb64, 
                'token': token,
                'usuario': usuario
            })
        
       
        if not clave_nueva:
            messages.error(request, 'La contraseña no puede estar vacía.')
            return render(request, 'login/password_reset_confirm.html', {
                'uidb64': uidb64, 
                'token': token,
                'usuario': usuario
            })
        
        if clave_nueva != clave_confirmar:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
            return render(request, 'login/password_reset_confirm.html', {
                'uidb64': uidb64, 
                'token': token,
                'usuario': usuario
            })
        
        if len(clave_nueva) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'login/password_reset_confirm.html', {
                'uidb64': uidb64, 
                'token': token,
                'usuario': usuario
            })
        
        
        usuario.clave = make_password(clave_nueva)
        usuario.save()
        
        messages.success(request, 'Tu contraseña ha sido actualizada correctamente. Inicia sesión con tu nueva contraseña.')
        return redirect('login')
    
    return render(request, 'login/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})


def password_reset_complete(request):
    """Confirma que la contraseña fue reseteada."""
    return render(request, 'login/password_reset_complete.html')
