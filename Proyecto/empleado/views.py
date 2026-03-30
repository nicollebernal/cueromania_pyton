from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from tienda.models import Usuario, Producto
from tienda.models import Personalizacion
from Carrito.carro import Carro


def login_view(request):
    if request.method == 'POST':
        gmail = request.POST.get('gmail', '').strip()
        clave = request.POST.get('clave', '').strip()

        print(f"Buscando - Gmail: '{gmail}', Clave: '{clave}'")

        usuario = Usuario.objects.filter(gmail=gmail).first()

        if usuario:
            print(f"Usuario encontrado: {usuario.primer_nombre}, Clave en BD: '{usuario.clave}'")

            if str(usuario.clave) == str(clave):
                request.session['usuario_id'] = usuario.id_usuario

                rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
                print(f"Rol encontrado: {rol_nombre}")

                if rol_nombre == 'administrador':
                    return redirect('administrador')

                elif rol_nombre == 'empleado':
                    return redirect('empleado')

                elif rol_nombre == 'cliente':
                    return redirect('cliente')

                else:
                    return render(request, 'login/login.html', {'error': 'Rol no válido'})
            else:
                print("Contraseña no coincide")
                return render(request, 'login/login.html', {
                    'error': 'Contraseña incorrecta'
                })
        else:
            print(f"No se encontró usuario con gmail: {gmail}")
            return render(request, 'login/login.html', {
                'error': 'Usuario no encontrado'
            })

    return render(request, 'login/login.html')


def admin_dashboard(request):
    return render(request, 'administrador/administrador.html')


def empleado_dashboard(request):
    """
    Dashboard del empleado con lista de productos e inventario.
    Incluye filtro de búsqueda.
    Si la búsqueda queda vacía, muestra toda la lista.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)

    query = request.GET.get('q', '').strip()

    productos = Producto.objects.all().order_by('id_producto')

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(id_categoria__nombre_categoria__icontains=query) |
            Q(id_marca__nombre_marca__icontains=query)
        )

    return render(request, 'empleado/empleado.html', {
        'usuario': usuario,
        'productos': productos,
        'query': query
    })
    
def inventario_empleado(request):
    """
    Vista del inventario del empleado con búsqueda.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)

    query = request.GET.get('q', '').strip()
    productos = Producto.objects.all().order_by('id_producto')

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )

    return render(request, 'empleado/inventario.html', {
        'usuario': usuario,
        'productos': productos,
        'query': query
    })


def editar_producto_empleado(request, producto_id):
    """
    Permite al empleado editar los datos del producto, incluido el stock.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    producto = get_object_or_404(Producto, id_producto=producto_id)

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre', producto.nombre)
        producto.precio = request.POST.get('precio', producto.precio)
        producto.talla = request.POST.get('talla', producto.talla)
        producto.estado = request.POST.get('estado', producto.estado)
        producto.descripcion = request.POST.get('descripcion', producto.descripcion)

        stock = request.POST.get('stock_producto', producto.stock_producto)
        try:
            producto.stock_producto = int(stock)
        except ValueError:
            messages.error(request, 'El stock debe ser un número válido.')
            return redirect('editar_producto_empleado', producto_id=producto.id_producto)

        if request.FILES.get('imagen'):
            producto.imagen = request.FILES.get('imagen')

        producto.save()
        messages.success(request, 'Producto actualizado correctamente.')
        return redirect('empleado')

    return render(request, 'empleado/editar_producto.html', {
        'producto': producto
    })


def sumar_stock(request, producto_id):
    """
    Suma stock rápidamente.
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id_producto=producto_id)
        cantidad = request.POST.get('cantidad', '0')

        try:
            cantidad = int(cantidad)
            if cantidad > 0:
                producto.stock_producto += cantidad
                producto.save()
                messages.success(request, f'Se agregaron {cantidad} unidades al stock.')
            else:
                messages.error(request, 'La cantidad debe ser mayor a 0.')
        except ValueError:
            messages.error(request, 'Cantidad inválida.')

    return redirect('empleado')


def restar_stock(request, producto_id):
    """
    Resta stock rápidamente sin dejar negativos.
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id_producto=producto_id)
        cantidad = request.POST.get('cantidad', '0')

        try:
            cantidad = int(cantidad)
            if cantidad > 0:
                if producto.stock_producto >= cantidad:
                    producto.stock_producto -= cantidad
                    producto.save()
                    messages.success(request, f'Se descontaron {cantidad} unidades del stock.')
                else:
                    messages.error(request, 'No puedes dejar el stock en negativo.')
            else:
                messages.error(request, 'La cantidad debe ser mayor a 0.')
        except ValueError:
            messages.error(request, 'Cantidad inválida.')

    return redirect('empleado')


def eliminar_producto_empleado(request, producto_id):
    """
    Elimina un producto.
    """
    producto = get_object_or_404(Producto, id_producto=producto_id)

    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('empleado')

    return render(request, 'empleado/eliminar_producto.html', {
        'producto': producto
    })


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
    producto = Producto.objects.get(id_producto=producto_id)
    return render(request, 'cliente/cliente.html', {
        'producto': producto
    })


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
    
def ventas_empleado(request):
    """
    Módulo de ventas presenciales.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    productos = Producto.objects.all().order_by('nombre')

    return render(request, 'empleado/ventas.html', {
        'usuario': usuario,
        'productos': productos
    })


def pedidos_personalizados(request):
    """
    Módulo de pedidos de personalización.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    personalizaciones = Personalizacion.objects.all().order_by('-fecha_solicitud')

    return render(request, 'empleado/pedidos_personalizados.html', {
        'usuario': usuario,
        'pedidos': personalizaciones
    })