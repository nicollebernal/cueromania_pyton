from django.shortcuts import render, redirect
from .models import Usuario, Producto, Rol
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

        # Si la BD tenía texto plano o MD5, migrar a hash Django una sola vez
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
        clave = make_password(request.POST['clave'])  # 🔑 aquí se cifra la clave
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
