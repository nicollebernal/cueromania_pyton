from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, F
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils import timezone
from tienda.models import Usuario, Producto, Venta, DetalleVenta
from tienda.models import Personalizacion, marcas, colores, genero, categoria, tipos_cierres
from Carrito.carro import Carro
from datetime import date
from functools import wraps
import json


# Decorador para validar rol de empleado o administrador
def requiere_rol_empleado(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('login')
        
        usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
        rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
        
        if rol_nombre not in ['empleado', 'administrador']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.method == 'POST':
        gmail = request.POST.get('gmail', '').strip()
        clave = request.POST.get('clave', '').strip()

        usuario = Usuario.objects.filter(gmail=gmail).first()

        if usuario:
            if usuario.verificar_clave(clave):
                request.session['usuario_id'] = usuario.id_usuario

                rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None

                if rol_nombre == 'administrador':
                    return redirect('administrador')

                elif rol_nombre == 'empleado':
                    return redirect('empleado')

                elif rol_nombre == 'cliente':
                    return redirect('cliente')

                else:
                    return render(request, 'login/login.html', {'error': 'Rol no válido'})
            else:
                return render(request, 'login/login.html', {
                    'error': 'Contraseña incorrecta'
                })
        else:
            return render(request, 'login/login.html', {
                'error': 'Usuario no encontrado'
            })

    return render(request, 'login/login.html')


@requiere_rol_empleado
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
    
@requiere_rol_empleado
def inventario_empleado(request):
    """
    Vista del inventario del empleado con búsqueda.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)

    query = request.GET.get('q', '').strip()
    productos = Producto.objects.all().order_by('id_producto').annotate(
        marca_nombre=F('id_marca__nombre_marca'),
        categoria_nombre=F('id_categoria__nombre_categoria')
    ).distinct()

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


@requiere_rol_empleado
def editar_producto_empleado(request, producto_id):
    """
    Permite al empleado editar los datos del producto, incluido el stock.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
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


@requiere_rol_empleado
def sumar_stock(request, producto_id):
    """
    Suma stock rápidamente.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('login')
    
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

    return redirect('inventario_empleado')


@requiere_rol_empleado
def restar_stock(request, producto_id):
    """
    Resta stock rápidamente sin dejar negativos.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('login')
    
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

    return redirect('inventario_empleado')


@requiere_rol_empleado
def eliminar_producto_empleado(request, producto_id):
    """
    Elimina un producto.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('login')
    
    producto = get_object_or_404(Producto, id_producto=producto_id)

    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('inventario_empleado')

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
    
@requiere_rol_empleado
def ventas_empleado(request):
    """
    Módulo de ventas presenciales.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.all().order_by('nombre')

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )

    facturas = Venta.objects.filter(id_usuario_id=usuario_id).order_by('-fecha_ventas', '-id_ventas')

    return render(request, 'empleado/ventas.html', {
        'usuario': usuario,
        'productos': productos,
        'query': query,
        'facturas': facturas
    })


@requiere_rol_empleado
def pedidos_personalizados(request):
    """
    Módulo de pedidos de personalización.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    personalizaciones = Personalizacion.objects.all().order_by('-fecha_solicitud').annotate(
        marca_nombre=F('id_marca__nombre_marca'),
        categoria_nombre=F('id_categoria__nombre_categoria'),
        color_nombre=F('id_color__nombre_color'),
        genero_nombre=F('id_genero__nombre_genero'),
        cliente_nombre=F('id_usuario__primer_nombre'),
        cliente_apellido=F('id_usuario__primer_apellido')
    ).distinct()
    
    marcas_list = marcas.objects.all()
    categorias_list = categoria.objects.all()
    generos_list = genero.objects.all()
    colores_list = colores.objects.all()
    clientes_list = Usuario.objects.filter(id_rol__nombre_rol='cliente')

    return render(request, 'empleado/pedidos_personalizados.html', {
        'usuario': usuario,
        'pedidos': personalizaciones,
        'marcas': marcas_list,
        'categorias': categorias_list,
        'generos': generos_list,
        'colores': colores_list,
        'clientes': clientes_list
    })


# ============ NUEVAS FUNCIONALIDADES ============

# ====== INVENTARIO ======
@requiere_rol_empleado
def crear_producto(request):
    """
    Crear un nuevo producto en el inventario.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        precio = request.POST.get('precio')
        talla = request.POST.get('talla')
        estado = request.POST.get('estado', 'disponible')
        stock = request.POST.get('stock_producto', 0)
        descripcion = request.POST.get('descripcion')
        id_marca = request.POST.get('id_marca')
        id_categoria = request.POST.get('id_categoria')
        id_genero = request.POST.get('id_genero')
        id_color = request.POST.get('id_color')
        id_tipo_cierre = request.POST.get('id_tipo_cierre')

        try:
            producto = Producto(
                nombre=nombre,
                precio=precio,
                talla=talla,
                estado=estado,
                stock_producto=int(stock),
                descripcion=descripcion,
                id_marca_id=id_marca,
                id_categoria_id=id_categoria,
                id_genero_id=id_genero,
                id_color_id=id_color,
                id_tipo_cierre_id=id_tipo_cierre
            )

            if request.FILES.get('imagen'):
                producto.imagen = request.FILES['imagen']

            producto.save()
            messages.success(request, f'Producto "{nombre}" creado correctamente.')
            return redirect('inventario_empleado')
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')

    marcas_list = marcas.objects.all()
    categorias_list = categoria.objects.all()
    generos_list = genero.objects.all()
    colores_list = colores.objects.all()
    tipos_cierres_list = tipos_cierres.objects.all()
    
    return render(request, 'empleado/crear_producto.html', {
        'marcas': marcas_list,
        'categorias': categorias_list,
        'generos': generos_list,
        'colores': colores_list,
        'tipos_cierres': tipos_cierres_list
    })


# ====== VENTAS CON CARRITO ======
@requiere_rol_empleado
def carrito_ventas(request):
    """
    Mostrar carrito de ventas temporal.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    carrito = request.session.get('carrito_ventas', {})
    
    productos_carrito = []
    total = 0
    
    for producto_id, datos in carrito.items():
        try:
            producto = Producto.objects.get(id_producto=int(producto_id))
            subtotal = datos['cantidad'] * datos['precio']
            productos_carrito.append({
                'id_producto': producto.id_producto,
                'nombre': producto.nombre,
                'cantidad': datos['cantidad'],
                'precio': datos['precio'],
                'subtotal': subtotal
            })
            total += subtotal
        except Producto.DoesNotExist:
            pass

    return render(request, 'empleado/carrito_ventas.html', {
        'usuario': usuario,
        'productos': productos_carrito,
        'total': total
    })


@requiere_rol_empleado
def agregar_al_carrito_venta(request, producto_id):
    """
    Agregar producto al carrito de ventas (retorna JSON para AJAX).
    """
    if request.method == 'POST':
        try:
            producto = get_object_or_404(Producto, id_producto=producto_id)
            cantidad = int(request.POST.get('cantidad', 1))
            
            if cantidad <= 0:
                return HttpResponse(json.dumps({'success': False, 'error': 'La cantidad debe ser mayor a 0.'}), content_type='application/json')
            
            if cantidad > producto.stock_producto:
                return HttpResponse(json.dumps({'success': False, 'error': f'Stock insuficiente. Disponibles: {producto.stock_producto}'}), content_type='application/json')

            if 'carrito_ventas' not in request.session:
                request.session['carrito_ventas'] = {}

            carrito = request.session['carrito_ventas']
            producto_id_str = str(producto_id)

            if producto_id_str in carrito:
                carrito[producto_id_str]['cantidad'] += cantidad
            else:
                carrito[producto_id_str] = {
                    'cantidad': cantidad,
                    'precio': float(producto.precio)
                }

            request.session.modified = True
            
            # Calcular total actual
            total = sum(datos['cantidad'] * datos['precio'] for datos in carrito.values())
            
            return HttpResponse(json.dumps({'success': True, 'message': f'{producto.nombre} agregado al carrito.', 'total': float(total)}), content_type='application/json')
        except Exception as e:
            return HttpResponse(json.dumps({'success': False, 'error': str(e)}), content_type='application/json')

    return HttpResponse(json.dumps({'success': False, 'error': 'Método no permitido'}), content_type='application/json')


@requiere_rol_empleado
def quitar_del_carrito_venta(request, producto_id):
    """
    Quitar producto del carrito de ventas (retorna JSON para AJAX).
    """
    try:
        if 'carrito_ventas' in request.session:
            carrito = request.session['carrito_ventas']
            producto_id_str = str(producto_id)
            
            if producto_id_str in carrito:
                del carrito[producto_id_str]
                request.session.modified = True
                
                # Calcular total actual
                total = sum(datos['cantidad'] * datos['precio'] for datos in carrito.values())
                
                return HttpResponse(json.dumps({'success': True, 'message': 'Producto removido del carrito.', 'total': float(total)}), content_type='application/json')
        
        return HttpResponse(json.dumps({'success': False, 'error': 'Producto no encontrado en el carrito'}), content_type='application/json')
    except Exception as e:
        return HttpResponse(json.dumps({'success': False, 'error': str(e)}), content_type='application/json')


@requiere_rol_empleado
def procesar_venta(request):
    """
    Procesar la venta y crear registro en base de datos.
    """
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('login')

        carrito = request.session.get('carrito_ventas', {})
        
        if not carrito:
            messages.error(request, 'El carrito está vacío.')
            return redirect('carrito_ventas')

        try:
            # Calcular total
            total = 0
            detalles_data = []
            
            for producto_id_str, datos in carrito.items():
                producto = Producto.objects.get(id_producto=int(producto_id_str))
                cantidad = datos['cantidad']
                precio = datos['precio']
                subtotal = cantidad * precio
                
                # Validar stock
                if cantidad > producto.stock_producto:
                    messages.error(request, f'Stock insuficiente para {producto.nombre}')
                    return redirect('carrito_ventas')
                
                detalles_data.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': precio,
                    'subtotal': subtotal
                })
                total += subtotal

            # Crear venta
            venta = Venta(
                fecha_ventas=date.today(),
                estado_venta='completada',
                total=total,
                id_usuario_id=usuario_id
            )
            venta.save()

            # Crear detalles y reducir stock
            for detalle in detalles_data:
                DetalleVenta.objects.create(
                    id_venta=venta,
                    id_producto=detalle['producto'],
                    cantidad=detalle['cantidad'],
                    precio_unitario=detalle['precio'],
                    cantidad_pagada=detalle['subtotal']
                )
                
                # Reducir stock
                detalle['producto'].stock_producto -= detalle['cantidad']
                detalle['producto'].save()

            # Limpiar carrito
            del request.session['carrito_ventas']
            request.session.modified = True

            messages.success(request, f'Venta #{venta.id_ventas} procesada correctamente.')
            return redirect('factura_venta', venta_id=venta.id_ventas)

        except Exception as e:
            messages.error(request, f'Error al procesar venta: {str(e)}')
            return redirect('carrito_ventas')

    return redirect('carrito_ventas')


@requiere_rol_empleado
def factura_venta(request, venta_id):
    """
    Mostrar y descargar factura en PDF.
    """
    venta = get_object_or_404(Venta, id_ventas=venta_id)
    detalles = DetalleVenta.objects.filter(id_venta=venta).select_related('id_producto')

    return render(request, 'empleado/factura_venta.html', {
        'venta': venta,
        'detalles': detalles
    })


@requiere_rol_empleado
def descargar_factura_pdf(request, venta_id):
    """
    Descargar factura como PDF.
    """
    venta = get_object_or_404(Venta, id_ventas=venta_id)
    detalles = DetalleVenta.objects.filter(id_venta=venta).select_related('id_producto')

    html_string = render_to_string('empleado/factura_pdf.html', {
        'venta': venta,
        'detalles': detalles
    })

    # Simulamos descarga de PDF (sin librería adicional)
    response = HttpResponse(html_string, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="factura_{venta.id_ventas}.html"'
    return response


# ====== PERSONALIZACIONES ======
@requiere_rol_empleado
def guardar_personalizacion(request):
    """
    Guardar una nueva solicitud de personalización.
    """
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('login')

        usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
        
        descripcion = request.POST.get('descripcion')
        id_usuario = request.POST.get('id_usuario')
        id_categoria = request.POST.get('id_categoria')
        id_color = request.POST.get('id_color')
        id_genero = request.POST.get('id_genero')
        id_marca = request.POST.get('id_marca')

        try:
            personalizacion = Personalizacion(
                descripcion=descripcion,
                fecha_solicitud=date.today(),
                id_usuario_id=id_usuario,
                id_categoria_id=id_categoria,
                id_color_id=id_color,
                id_genero_id=id_genero,
                id_marca_id=id_marca
            )

            if request.FILES.get('imagen_personalizacion'):
                personalizacion.imagen_personalizacion = request.FILES['imagen_personalizacion']

            personalizacion.save()
            messages.success(request, 'Personalización guardada correctamente.')
            return redirect('pedidos_personalizados')
        except Exception as e:
            messages.error(request, f'Error al guardar: {str(e)}')

    return redirect('pedidos_personalizados')


@requiere_rol_empleado
def editar_personalizacion(request, personalizacion_id):
    """
    Editar una personalización existente.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('login')
    
    personalizacion_qs = Personalizacion.objects.filter(id_personalizacion=personalizacion_id)
    personalizacion = personalizacion_qs.first()
    if not personalizacion:
        raise Http404('Personalización no encontrada')

    if request.method == 'POST':
        personalizacion.descripcion = request.POST.get('descripcion', personalizacion.descripcion)
        personalizacion.id_usuario_id = request.POST.get('id_usuario', personalizacion.id_usuario_id)
        personalizacion.id_categoria_id = request.POST.get('id_categoria', personalizacion.id_categoria_id)
        personalizacion.id_color_id = request.POST.get('id_color', personalizacion.id_color_id)
        personalizacion.id_genero_id = request.POST.get('id_genero', personalizacion.id_genero_id)
        personalizacion.id_marca_id = request.POST.get('id_marca', personalizacion.id_marca_id)

        if request.FILES.get('imagen_personalizacion'):
            personalizacion.imagen_personalizacion = request.FILES['imagen_personalizacion']

        try:
            personalizacion.save()
            messages.success(request, 'Personalización actualizada correctamente.')
            return redirect('pedidos_personalizados')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')

    clientes_list = Usuario.objects.filter(id_rol__nombre_rol='cliente')
    marcas_list = marcas.objects.all()
    categorias_list = categoria.objects.all()
    generos_list = genero.objects.all()
    colores_list = colores.objects.all()

    return render(request, 'empleado/editar_personalizacion.html', {
        'personalizacion': personalizacion,
        'clientes': clientes_list,
        'marcas': marcas_list,
        'categorias': categorias_list,
        'generos': generos_list,
        'colores': colores_list
    })


@requiere_rol_empleado
def eliminar_personalizacion(request, personalizacion_id):
    """
    Eliminar una personalización.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    rol_nombre = usuario.id_rol.nombre_rol if usuario.id_rol else None
    
    if rol_nombre not in ['empleado', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('login')
    
    personalizacion_qs = Personalizacion.objects.filter(id_personalizacion=personalizacion_id)
    personalizacion = personalizacion_qs.first()
    if not personalizacion:
        raise Http404('Personalización no encontrada')

    if request.method == 'POST':
        try:
            personalizacion.delete()
            messages.success(request, 'Personalización eliminada correctamente.')
            return redirect('pedidos_personalizados')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')

    return render(request, 'empleado/eliminar_personalizacion.html', {
        'personalizacion': personalizacion
    })