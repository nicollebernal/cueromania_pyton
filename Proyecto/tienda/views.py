from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.db.models import Avg, OuterRef, Subquery
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

            Personalizacion.objects.create(
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