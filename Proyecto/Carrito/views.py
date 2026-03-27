from django.shortcuts import redirect, render
from Carrito.carro import Carro
from tienda.models import Producto
from django.http import JsonResponse
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