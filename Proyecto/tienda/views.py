from datetime import date

from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Usuario, Producto, Rol, Personalizacion, categoria, colores, marcas, genero
from django.contrib.auth.hashers import make_password
from Carrito.carro import Carro


def login_view(request):
    if request.method == 'POST':
        gmail = request.POST.get('gmail', '').strip()
        clave = request.POST.get('clave', '')

        usuario = (
            Usuario.objects.filter(gmail__iexact=gmail)
            .select_related('id_rol')
            .first()
        )

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


def empleado_dashboard(request):
    return render(request, 'Empleado/empleado.html')


def cliente_dashboard(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    productos = Producto.objects.all()
    carro = Carro(request)
    for producto in productos:
        producto.cantidad_en_carro = carro.carro.get(str(producto.id_producto), {}).get('cantidad', 0)
    return render(request, 'cliente/cliente.html', {
        'usuario': usuario,
        'productos': productos
    })


def cliente_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    mensaje = ''

    if request.method == 'POST':
        usuario.primer_nombre = request.POST.get('primer_nombre', usuario.primer_nombre).strip()
        usuario.segundo_nombre = request.POST.get('segundo_nombre', usuario.segundo_nombre).strip()
        usuario.primer_apellido = request.POST.get('primer_apellido', usuario.primer_apellido).strip()
        usuario.segundo_apellido = request.POST.get('segundo_apellido', usuario.segundo_apellido).strip()
        usuario.direccion = request.POST.get('direccion', usuario.direccion).strip()
        usuario.contacto = request.POST.get('contacto', usuario.contacto).strip()
        usuario.gmail = request.POST.get('gmail', usuario.gmail).strip()
        usuario.save(update_fields=['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'direccion', 'contacto', 'gmail'])
        mensaje = 'Perfil actualizado correctamente.'

    return render(request, 'cliente/perfil.html', {
        'usuario': usuario,
        'mensaje': mensaje,
    })


def logout_view(request):
    request.session.flush()
    return redirect('/')


def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'cliente/cliente.html', {
        'productos': productos
    })

def agregar(request, producto_id):
    productos = Producto.objects.get(id_producto=producto_id)

    return render(request, 'cliente/cliente.html', {
        'producto': productos})


def filtrar_producto(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.all()

    if query:
        productos = productos.filter(nombre__icontains=query)

    carro = Carro(request)
    for producto in productos:
        producto.cantidad_en_carro = carro.carro.get(str(producto.id_producto), {}).get('cantidad', 0)

    return render(request, 'cliente/cliente.html', {
        'usuario': usuario,
        'productos': productos,
        'query': query
    })

def registrar_usuario(request):
    if request.method == 'POST':
        id_usuario = request.POST ['id_usuario']
        primer_nombre = request.POST['primer_nombre']
        segundo_nombre = request.POST['segundo_nombre']
        primer_apellido = request.POST['primer_apellido']
        segundo_apellido = request.POST['segundo_apellido']
        direccion = request.POST['direccion']
        contacto = request.POST['contacto']
        gmail = request.POST['gmail']
        clave = make_password(request.POST['clave'])
        rol_cliente = Rol.objects.get(nombre_rol='cliente')

        usuario = Usuario.objects.create(
            id_usuario=id_usuario,
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,
            primer_apellido=primer_apellido,
            segundo_apellido=segundo_apellido,
            direccion=direccion,
            contacto=contacto,
            gmail=gmail,
            clave=clave,
            id_rol=rol_cliente
        )
        usuario.save()
        return redirect('login')

    roles = Rol.objects.all()
    return render(request, 'login/registro.html', {'roles': roles})


def personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    personalizaciones = Personalizacion.objects.filter(id_usuario=usuario)

    categorias = categoria.objects.all()
    colores_lista = colores.objects.all()
    marcas_lista = marcas.objects.all()
    generos_lista = genero.objects.all()

    return render(request, 'cliente/personalizacion.html', {
        'usuario': usuario,
        'personalizaciones': personalizaciones,
        'categorias': categorias,
        'colores': colores_lista,
        'marcas': marcas_lista,
        'generos': generos_lista,
    })


def crear_personalizacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        fecha_solicitud = request.POST.get('fecha_solicitud')
        if fecha_solicitud:
            try:
                fecha_solicitud = date.fromisoformat(fecha_solicitud)
            except ValueError:
                fecha_solicitud = date.today()
        else:
            fecha_solicitud = date.today()

        categoria_id = request.POST.get('id_categoria')
        color_id = request.POST.get('id_color')
        marca_id = request.POST.get('id_marca')
        genero_id = request.POST.get('id_genero')
        imagen_personalizacion = request.FILES.get('imagen_personalizacion')

        try:
            categoria_obj = categoria.objects.get(pk=categoria_id)
            color_obj = colores.objects.get(pk=color_id)
            marca_obj = marcas.objects.get(pk=marca_id)
            genero_obj = genero.objects.get(pk=genero_id)
        except (categoria.DoesNotExist, colores.DoesNotExist, marcas.DoesNotExist, genero.DoesNotExist, TypeError, ValueError):
            return redirect('personalizacion')

        Personalizacion.objects.create(
            id_usuario=usuario,
            descripcion=descripcion,
            imagen_personalizacion=imagen_personalizacion,
            fecha_solicitud=fecha_solicitud,
            id_categoria=categoria_obj,
            id_color=color_obj,
            id_marca=marca_obj,
            id_genero=genero_obj,
        )

    return redirect('personalizacion')