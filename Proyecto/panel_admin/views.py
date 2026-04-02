from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from tienda.models import (
    Producto,
    Usuario,
    marcas,
    colores,
    categoria,
    genero,
    tipos_cierres,
    Venta,
    DetalleVenta,
    Pago,
    Personalizacion,
)

from .decorators import solo_administrador
from .forms import (
    ProductoForm,
    UsuarioAdminForm,
    MarcaForm,
    ColorForm,
    CategoriaForm,
    GeneroForm,
    TipoCierreForm,
    VentaForm,
    VentaEditForm,
    PagoForm,
    PersonalizacionForm,
)


@solo_administrador
def dashboard(request):
    stats = {
        'productos': Producto.objects.count(),
        'usuarios': Usuario.objects.count(),
        'marcas': marcas.objects.count(),
        'colores': colores.objects.count(),
        'ventas': Venta.objects.count(),
        'pagos': Pago.objects.count(),
        'personalizaciones': Personalizacion.objects.count(),
    }
    return render(
        request,
        'panel_admin/dashboard.html',
        {'stats': stats, 'usuario': request.admin_usuario},
    )





@solo_administrador
def productos_lista(request):
    productos = Producto.objects.select_related(
        'id_marca', 'id_categoria', 'id_color', 'id_genero', 'id_tipo_cierre'
    ).order_by('-id_producto')
    lista_colores = colores.objects.all().order_by('nombre_color')
    return render(
        request,
        'panel_admin/productos_lista.html',
        {
            'productos': productos,
            'lista_colores': lista_colores,
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def productos_lista_pdf(request):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        messages.error(
            request,
            'Para exportar PDF instale reportlab en el entorno: pip install reportlab',
        )
        return redirect('panel_productos')

    productos = Producto.objects.select_related(
        'id_marca', 'id_categoria', 'id_color'
    ).order_by('-id_producto')
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph('Cueromania — Productos (administrador)', styles['Title']))
    elements.append(Spacer(1, 12))
    data = [['ID', 'Nombre', 'Categoría', 'Marca', 'Color', 'Stock', 'Precio', 'Estado']]
    for p in productos:
        data.append(
            [
                str(p.id_producto),
                p.nombre[:40],
                p.id_categoria.nombre_categoria if p.id_categoria_id else '',
                p.id_marca.nombre_marca if p.id_marca_id else '',
                p.id_color.nombre_color if p.id_color_id else '',
                str(p.stock_producto),
                str(p.precio),
                p.estado,
            ]
        )
    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    elements.append(t)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="productos_cueromania.pdf"'
    return response


@solo_administrador
def producto_nuevo(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('panel_productos')
    else:
        form = ProductoForm()
    return render(
        request,
        'panel_admin/producto_form.html',
        {'form': form, 'titulo': 'Nuevo producto', 'usuario': request.admin_usuario},
    )


@solo_administrador
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('panel_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(
        request,
        'panel_admin/producto_form.html',
        {
            'form': form,
            'titulo': 'Editar producto',
            'producto': producto,
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('panel_productos')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar producto',
            'objeto': producto,
            'volver': 'panel_productos',
            'usuario': request.admin_usuario,
        },
    )




@solo_administrador
def usuarios_lista(request):
    usuarios = Usuario.objects.select_related('id_rol').order_by('-id_usuario')
    return render(
        request,
        'panel_admin/usuarios_lista.html',
        {'usuarios': usuarios, 'usuario': request.admin_usuario},
    )


@solo_administrador
def usuario_nuevo(request):
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, creating=True)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado.')
            return redirect('panel_usuarios')
    else:
        form = UsuarioAdminForm(creating=True)
    return render(
        request,
        'panel_admin/usuario_form.html',
        {'form': form, 'titulo': 'Nuevo usuario', 'usuario': request.admin_usuario},
    )


@solo_administrador
def usuario_editar(request, pk):
    u = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado.')
            return redirect('panel_usuarios')
    else:
        form = UsuarioAdminForm(instance=u)
    return render(
        request,
        'panel_admin/usuario_form.html',
        {'form': form, 'titulo': 'Editar usuario', 'edit_usuario': u, 'usuario': request.admin_usuario},
    )


@solo_administrador
def usuario_eliminar(request, pk):
    u = get_object_or_404(Usuario, pk=pk)
    if u.id_usuario == request.admin_usuario.id_usuario:
        messages.error(request, 'No puede eliminar su propia cuenta.')
        return redirect('panel_usuarios')
    if request.method == 'POST':
        u.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('panel_usuarios')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar usuario',
            'objeto': u,
            'volver': 'panel_usuarios',
            'usuario': request.admin_usuario,
        },
    )




@solo_administrador
def marcas_lista(request):
    items = marcas.objects.all().order_by('nombre_marca')
    return render(
        request,
        'panel_admin/catalogo_lista.html',
        {
            'titulo': 'Marcas',
            'items': items,
            'campo': 'nombre_marca',
            'url_nuevo': 'panel_marca_nueva',
            'url_editar': 'panel_marca_editar',
            'url_eliminar': 'panel_marca_eliminar',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def marca_form(request, pk=None):
    inst = get_object_or_404(marcas, pk=pk) if pk else None
    if request.method == 'POST':
        form = MarcaForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca guardada.')
            return redirect('panel_marcas')
    else:
        form = MarcaForm(instance=inst)
    return render(
        request,
        'panel_admin/catalogo_form.html',
        {
            'form': form,
            'titulo': 'Editar marca' if pk else 'Nueva marca',
            'volver': 'panel_marcas',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def marca_eliminar(request, pk):
    obj = get_object_or_404(marcas, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Marca eliminada.')
        return redirect('panel_marcas')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar marca',
            'objeto': obj,
            'volver': 'panel_marcas',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def colores_lista(request):
    items = colores.objects.all().order_by('nombre_color')
    return render(
        request,
        'panel_admin/catalogo_lista.html',
        {
            'titulo': 'Colores',
            'items': items,
            'campo': 'nombre_color',
            'url_nuevo': 'panel_color_nuevo',
            'url_editar': 'panel_color_editar',
            'url_eliminar': 'panel_color_eliminar',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def color_form(request, pk=None):
    inst = get_object_or_404(colores, pk=pk) if pk else None
    if request.method == 'POST':
        form = ColorForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Color guardado.')
            return redirect('panel_colores')
    else:
        form = ColorForm(instance=inst)
    return render(
        request,
        'panel_admin/catalogo_form.html',
        {
            'form': form,
            'titulo': 'Editar color' if pk else 'Nuevo color',
            'volver': 'panel_colores',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def color_eliminar(request, pk):
    obj = get_object_or_404(colores, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Color eliminado.')
        return redirect('panel_colores')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar color',
            'objeto': obj,
            'volver': 'panel_colores',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def categorias_lista(request):
    items = categoria.objects.all().order_by('nombre_categoria')
    return render(
        request,
        'panel_admin/catalogo_lista.html',
        {
            'titulo': 'Categorías',
            'items': items,
            'campo': 'nombre_categoria',
            'url_nuevo': 'panel_categoria_nueva',
            'url_editar': 'panel_categoria_editar',
            'url_eliminar': 'panel_categoria_eliminar',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def categoria_form(request, pk=None):
    inst = get_object_or_404(categoria, pk=pk) if pk else None
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría guardada.')
            return redirect('panel_categorias')
    else:
        form = CategoriaForm(instance=inst)
    return render(
        request,
        'panel_admin/catalogo_form.html',
        {
            'form': form,
            'titulo': 'Editar categoría' if pk else 'Nueva categoría',
            'volver': 'panel_categorias',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def categoria_eliminar(request, pk):
    obj = get_object_or_404(categoria, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Categoría eliminada.')
        return redirect('panel_categorias')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar categoría',
            'objeto': obj,
            'volver': 'panel_categorias',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def generos_lista(request):
    items = genero.objects.all().order_by('nombre_genero')
    return render(
        request,
        'panel_admin/catalogo_lista.html',
        {
            'titulo': 'Géneros',
            'items': items,
            'campo': 'nombre_genero',
            'url_nuevo': 'panel_genero_nuevo',
            'url_editar': 'panel_genero_editar',
            'url_eliminar': 'panel_genero_eliminar',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def genero_form(request, pk=None):
    inst = get_object_or_404(genero, pk=pk) if pk else None
    if request.method == 'POST':
        form = GeneroForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Género guardado.')
            return redirect('panel_generos')
    else:
        form = GeneroForm(instance=inst)
    return render(
        request,
        'panel_admin/catalogo_form.html',
        {
            'form': form,
            'titulo': 'Editar género' if pk else 'Nuevo género',
            'volver': 'panel_generos',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def genero_eliminar(request, pk):
    obj = get_object_or_404(genero, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Género eliminado.')
        return redirect('panel_generos')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar género',
            'objeto': obj,
            'volver': 'panel_generos',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def tipos_cierre_lista(request):
    items = tipos_cierres.objects.all().order_by('tipo_cierre')
    return render(
        request,
        'panel_admin/catalogo_lista.html',
        {
            'titulo': 'Tipos de cierre',
            'items': items,
            'campo': 'tipo_cierre',
            'url_nuevo': 'panel_tipo_cierre_nuevo',
            'url_editar': 'panel_tipo_cierre_editar',
            'url_eliminar': 'panel_tipo_cierre_eliminar',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def tipo_cierre_form(request, pk=None):
    inst = get_object_or_404(tipos_cierres, pk=pk) if pk else None
    if request.method == 'POST':
        form = TipoCierreForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de cierre guardado.')
            return redirect('panel_tipos_cierre')
    else:
        form = TipoCierreForm(instance=inst)
    return render(
        request,
        'panel_admin/catalogo_form.html',
        {
            'form': form,
            'titulo': 'Editar tipo de cierre' if pk else 'Nuevo tipo de cierre',
            'volver': 'panel_tipos_cierre',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def tipo_cierre_eliminar(request, pk):
    obj = get_object_or_404(tipos_cierres, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Tipo de cierre eliminado.')
        return redirect('panel_tipos_cierre')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar tipo de cierre',
            'objeto': obj,
            'volver': 'panel_tipos_cierre',
            'usuario': request.admin_usuario,
        },
    )


# ——— Ventas ———


@solo_administrador
def ventas_lista(request):
    ventas = (
        Venta.objects.select_related('id_usuario')
        .prefetch_related(
            Prefetch(
                'detalles',
                queryset=DetalleVenta.objects.select_related('id_producto'),
            )
        )
        .order_by('-id_ventas')
    )
    return render(
        request,
        'panel_admin/ventas_lista.html',
        {'ventas': ventas, 'usuario': request.admin_usuario},
    )


@solo_administrador
def venta_nuevo(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save()
            prod = form.cleaned_data.get('producto_inicial')
            cant = form.cleaned_data.get('cantidad_inicial')
            if prod and cant:
                sub = Decimal(prod.precio) * cant
                DetalleVenta.objects.create(
                    id_venta=venta,
                    id_producto=prod,
                    cantidad=cant,
                    precio_unitario=prod.precio,
                    cantidad_pagada=sub,
                )
            messages.success(request, 'Venta registrada correctamente.')
            return redirect('panel_ventas')
    else:
        form = VentaForm(
            initial={
                'fecha_ventas': date.today(),
                'estado_venta': 'pendiente',
            }
        )
    return render(
        request,
        'panel_admin/venta_form.html',
        {'form': form, 'titulo': 'Nueva venta', 'usuario': request.admin_usuario},
    )


@solo_administrador
def venta_ver(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related('id_usuario').prefetch_related(
            Prefetch(
                'detalles',
                queryset=DetalleVenta.objects.select_related('id_producto'),
            )
        ),
        pk=pk,
    )
    return render(
        request,
        'panel_admin/venta_ver.html',
        {'venta': venta, 'usuario': request.admin_usuario},
    )


@solo_administrador
def venta_editar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaEditForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada.')
            return redirect('panel_ventas')
    else:
        form = VentaEditForm(instance=venta)
    return render(
        request,
        'panel_admin/venta_editar.html',
        {'form': form, 'venta': venta, 'usuario': request.admin_usuario},
    )


@solo_administrador
def venta_eliminar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()
        messages.success(request, 'Venta eliminada.')
        return redirect('panel_ventas')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar venta',
            'objeto': venta,
            'volver': 'panel_ventas',
            'usuario': request.admin_usuario,
        },
    )


@solo_administrador
def venta_entregar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    venta.estado_venta = 'entregado'
    venta.save(update_fields=['estado_venta'])
    messages.success(request, 'Estado actualizado a entregado.')
    return redirect('panel_ventas')


# ——— Pagos ———


@solo_administrador
def pagos_lista(request):
    pagos = Pago.objects.select_related('id_venta').order_by('-id_pagos')
    return render(
        request,
        'panel_admin/pagos_lista.html',
        {'pagos': pagos, 'usuario': request.admin_usuario},
    )


@solo_administrador
def pago_nuevo(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pago creado.')
            return redirect('panel_pagos')
    else:
        form = PagoForm()
    return render(
        request,
        'panel_admin/pago_form.html',
        {'form': form, 'titulo': 'Crear pago', 'usuario': request.admin_usuario},
    )


@solo_administrador
def pago_editar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    if request.method == 'POST':
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pago actualizado.')
            return redirect('panel_pagos')
    else:
        form = PagoForm(instance=pago)
    return render(
        request,
        'panel_admin/pago_form.html',
        {'form': form, 'titulo': 'Editar pago', 'pago': pago, 'usuario': request.admin_usuario},
    )


@solo_administrador
def pago_eliminar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    if request.method == 'POST':
        pago.delete()
        messages.success(request, 'Pago eliminado.')
        return redirect('panel_pagos')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar pago',
            'objeto': pago,
            'volver': 'panel_pagos',
            'usuario': request.admin_usuario,
        },
    )


# ——— Personalización ———


@solo_administrador
def personalizacion_lista(request):
    qs = (
        Personalizacion.objects.select_related(
            'id_usuario', 'id_categoria', 'id_color', 'id_marca', 'id_genero'
        )
        .order_by('-id_personalizacion')
    )
    return render(
        request,
        'panel_admin/personalizacion_lista.html',
        {'items': qs, 'usuario': request.admin_usuario},
    )


@solo_administrador
def personalizacion_ver(request, pk):
    obj = get_object_or_404(
        Personalizacion.objects.select_related(
            'id_usuario', 'id_categoria', 'id_color', 'id_marca', 'id_genero'
        ),
        pk=pk,
    )
    return render(
        request,
        'panel_admin/personalizacion_ver.html',
        {'p': obj, 'usuario': request.admin_usuario},
    )


@solo_administrador
def personalizacion_editar(request, pk):
    obj = get_object_or_404(Personalizacion, pk=pk)
    if request.method == 'POST':
        form = PersonalizacionForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personalización actualizada.')
            return redirect('panel_personalizacion')
    else:
        form = PersonalizacionForm(instance=obj)
    return render(
        request,
        'panel_admin/personalizacion_form.html',
        {'form': form, 'titulo': 'Editar personalización', 'obj': obj, 'usuario': request.admin_usuario},
    )


@solo_administrador
def personalizacion_eliminar(request, pk):
    obj = get_object_or_404(Personalizacion, pk=pk)
    if request.method == 'POST':
        if obj.imagen_personalizacion:
            obj.imagen_personalizacion.delete(save=False)
        obj.delete()
        messages.success(request, 'Personalización eliminada.')
        return redirect('panel_personalizacion')
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar personalización',
            'objeto': obj,
            'volver': 'panel_personalizacion',
            'usuario': request.admin_usuario,
        },
    )
 

@solo_administrador
def valoraciones_lista(request):
    from tienda.models import Valoracion
    

    opiniones = Valoracion.objects.all().order_by('-id_valoracion')
    
    return render(
        request,
        'panel_admin/valoraciones_lista.html',
        {
            'opiniones': opiniones, # Asegúrate que sea plural
            'usuario': request.admin_usuario,
            'titulo': 'Opiniones de Clientes'
        },
    )
@solo_administrador
def valoracion_eliminar(request, pk):
    from tienda.models import Valoracion
    opinion = get_object_or_404(Valoracion, pk=pk)
    
    if request.method == 'POST':
        opinion.delete()
        messages.success(request, 'La opinión ha sido eliminada.')
        return redirect('panel_valoraciones') 
        
    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar Valoración',
            'objeto': f"Opinión de {opinion.id_usuario.primer_nombre} sobre {opinion.id_producto.nombre}",
            'volver': 'panel_valoraciones',
            'usuario': request.admin_usuario,
        },
    )