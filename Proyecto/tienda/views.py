from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from .models import (
    Usuario, Producto, Rol, Personalizacion, 
    Valoracion, Venta, DetalleVenta, 
    categoria, colores, marcas, genero,
)
from Carrito.carro import Carro

# --- VISTAS DE ACCESO Y PERFIL ---

def login_view(request):
    if request.method == 'POST':
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
    if request.method == 'POST':
        id_usuario = request.POST['id_usuario']
        clave = make_password(request.POST['clave'])
        rol_cliente = Rol.objects.get(nombre_rol='cliente')

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

# --- DASHBOARDS Y TIENDA ---

def empleado_dashboard(request):
    return render(request, 'Empleado/empleado.html')

def cliente_dashboard(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    productos = Producto.objects.all()
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
    productos = Producto.objects.filter(nombre__icontains=query) if query else Producto.objects.all()
    carro = Carro(request)
    for producto in productos:
        producto.cantidad_en_carro = carro.carro.get(str(producto.id_producto), {}).get('cantidad', 0)
    return render(request, 'cliente/cliente.html', {'usuario': usuario, 'productos': productos, 'query': query})

# --- PERSONALIZACIÓN Y VALORACIONES ---

def personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    return render(request, 'cliente/personalizacion.html', {
        'usuario': usuario,
        'personalizaciones': Personalizacion.objects.filter(id_usuario=usuario),
        'categorias': categoria.objects.all(),
        'colores': colores.objects.all(),
        'marcas': marcas.objects.all(),
        'generos': genero.objects.all(),
    })

def crear_personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    if request.method == 'POST':
        Personalizacion.objects.create(
            id_usuario=Usuario.objects.get(id_usuario=usuario_id),
            descripcion=request.POST.get('descripcion', ''),
            id_categoria=categoria.objects.get(pk=request.POST.get('id_categoria')),
            id_color=colores.objects.get(pk=request.POST.get('id_color')),
            id_marca=marcas.objects.get(pk=request.POST.get('id_marca')),
            id_genero=genero.objects.get(pk=request.POST.get('id_genero')),
            imagen_personalizacion=request.FILES.get('imagen_personalizacion')
        )
    return redirect('personalizacion')

def valoraciones(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    reviews = Valoracion.objects.filter(id_usuario=usuario).select_related('id_producto')
    reviewed_ids = set(reviews.values_list('id_producto_id', flat=True))
    compras = DetalleVenta.objects.filter(id_venta__id_usuario=usuario).select_related('id_producto')
    productos_pendientes = [d.id_producto for d in compras if d.id_producto.id_producto not in reviewed_ids]
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
                # Si tu modelo tiene un campo para imagen, descomenta la línea de abajo:
                # imagen_valoracion=foto, 
                fecha_puntuacion=date.today()
            )
            messages.success(request, '¡Gracias por tu valoración!')
            return redirect('valoraciones')
        else:
            messages.error(request, 'Debes seleccionar una puntuación.')

    return render(request, 'cliente/crear_valoracion.html', {'producto': producto})
def nosotros(request):
    return render(request, 'cliente/nosotros.html')