import json
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import JsonResponse

from Carrito.carro import Carro
from tienda.models import Producto, Usuario, Venta, DetalleVenta, Pago
def carro(request):
    carro = Carro(request)
    productos = Producto.objects.filter(id_producto__in=carro.carro.keys())
    for producto in productos:
        entry = carro.carro[str(producto.id_producto)]
        producto.cantidad = entry.get('cantidad', entry.get('stock_producto', 0))
        if 'stock_producto' in entry:
            entry['cantidad'] = producto.cantidad
            entry.pop('stock_producto', None)
            carro.guardar()
        producto.total_carrito = producto.precio * producto.cantidad
    total = sum(producto.total_carrito for producto in productos)
    return render(request, 'carrito.html', {'carro': carro, 'productos': productos, 'total': total})


def checkout(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión para completar la compra.')
        return redirect('login')

    usuario = Usuario.objects.get(id_usuario=usuario_id)
    carro = Carro(request)
    if not carro.carro:
        messages.error(request, 'El carrito está vacío. Agrega al menos una chaqueta antes de pagar.')
        return redirect('carro')

    productos = Producto.objects.filter(id_producto__in=carro.carro.keys())
    items = []
    total = Decimal('0.00')

    for producto in productos:
        entry = carro.carro[str(producto.id_producto)]
        cantidad = int(entry.get('cantidad', 1))
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', '').strip()
        opcion_pago = request.POST.get('opcion_pago', '').strip()
        personalizacion = request.POST.get('personalizacion', '').strip()

        if metodo_pago not in ['Nequi', 'Bancolombia', 'Daviplata']:
            messages.error(request, 'Selecciona un método de pago válido.')
            return render(request, 'checkout.html', {
                'usuario': usuario,
                'items': items,
                'total': total,
                'metodo_pago': metodo_pago,
                'opcion_pago': opcion_pago,
                'personalizacion': personalizacion,
            })

        venta = Venta.objects.create(
            fecha_ventas=date.today(),
            estado_venta='Pendiente',
            total=total,
            id_usuario=usuario,
        )

        for item in items:
            producto = item['producto']
            cantidad = item['cantidad']
            subtotal = item['subtotal']

            DetalleVenta.objects.create(
                cantidad=cantidad,
                cantidad_pagada=subtotal,
                precio_unitario=producto.precio,
                id_venta=venta,
                id_producto=producto,
            )

            producto.stock_producto = max(producto.stock_producto - cantidad, 0)
            producto.save(update_fields=['stock_producto'])

        Pago.objects.create(
            precio=total,
            estado_pago='Por validar',
            metodo_pagos=metodo_pago,
            opcion_pagos=opcion_pago,
            id_venta=venta,
        )

        carro.limpiar()

        return render(request, 'confirmacion_compra.html', {
            'venta': venta,
            'items': items,
            'total': total,
            'metodo_pago': metodo_pago,
            'opcion_pago': opcion_pago,
            'personalizacion': personalizacion,
        })

    return render(request, 'checkout.html', {
        'usuario': usuario,
        'items': items,
        'total': total,
    })


def checkout_api(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'success': False, 'error': 'Debes iniciar sesión para completar la compra.'}, status=401)

    try:
        usuario = Usuario.objects.get(id_usuario=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado.'}, status=401)

    carro = Carro(request)
    if not carro.carro:
        return JsonResponse({'success': False, 'error': 'El carrito está vacío.'}, status=400)

    productos = Producto.objects.filter(id_producto__in=carro.carro.keys())
    items = []
    total = Decimal('0.00')

    for producto in productos:
        entry = carro.carro.get(str(producto.id_producto), {})
        cantidad = int(entry.get('cantidad', 1))
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'talla': producto.talla,
            'precio': str(producto.precio),
            'cantidad': cantidad,
            'subtotal': str(subtotal),
        })

    if request.method == 'POST':
        try:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' in content_type:
                payload = json.loads(request.body.decode('utf-8') or '{}')
            else:
                payload = request.POST
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

        metodo_pago = str(payload.get('metodo_pago', '')).strip()
        opcion_pago = str(payload.get('opcion_pago', '')).strip()
        personalizacion = str(payload.get('personalizacion', '')).strip()

        if metodo_pago not in ['Nequi', 'Bancolombia', 'Daviplata']:
            return JsonResponse({'success': False, 'error': 'Selecciona un método de pago válido.'}, status=400)

        venta = Venta.objects.create(
            fecha_ventas=date.today(),
            estado_venta='Pendiente',
            total=total,
            id_usuario=usuario,
        )

        for item in items:
            producto = Producto.objects.get(id_producto=item['id_producto'])
            cantidad = item['cantidad']
            subtotal = Decimal(item['subtotal'])
            DetalleVenta.objects.create(
                cantidad=cantidad,
                cantidad_pagada=subtotal,
                precio_unitario=producto.precio,
                id_venta=venta,
                id_producto=producto,
            )
            producto.stock_producto = max(producto.stock_producto - cantidad, 0)
            producto.save(update_fields=['stock_producto'])

        Pago.objects.create(
            precio=total,
            estado_pago='Por validar',
            metodo_pagos=metodo_pago,
            opcion_pagos=opcion_pago,
            id_venta=venta,
        )

        carro.limpiar()

        return JsonResponse({
            'success': True,
            'message': 'Compra registrada con éxito.',
            'venta_id': venta.id_ventas,
            'total': str(total),
            'metodo_pago': metodo_pago,
            'opcion_pago': opcion_pago,
            'personalizacion': personalizacion,
        }, status=201)

    return JsonResponse({
        'success': True,
        'items': items,
        'total': str(total),
        'payment_methods': ['Nequi', 'Bancolombia', 'Daviplata'],
    })


def agregar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    carro.agregar(producto)
    return redirect('carro')

def sumar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    carro.agregar(producto)
    cantidad = carro.carro.get(str(producto_id), {}).get('cantidad', 0)
    return JsonResponse({'cantidad': cantidad})


def eliminar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    carro.eliminar(producto)
    return redirect ('carro')

def restar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    carro.restar(producto)
    cantidad = carro.carro.get(str(producto_id), {}).get('cantidad', 0)
    return JsonResponse({'cantidad':cantidad})

def limpiar(request):
    carro = Carro(request)
    carro.limpiar()
    return redirect('carro')

def editar(request, producto_id):
    carro = Carro(request)
    producto = Producto.objects.get(id_producto=producto_id)
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad > 0:
            carro.carro[str(producto_id)]['cantidad'] = cantidad
            carro.guardar()
        else:
            carro.eliminar(producto)
        return redirect('carro')
    
    return render(request, 'editar.html', {'producto': producto})