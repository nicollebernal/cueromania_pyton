from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from tienda.models import (
    Usuario,
    Producto,
    marcas,
    colores,
    categoria,
    genero,
    tipos_cierres,
    Venta,
    Pago,
    Personalizacion,
)


def _aplicar_estilos_bootstrap(form):
    for field in form.fields.values():
        w = field.widget
        if isinstance(w, forms.Select):
            w.attrs.setdefault('class', 'form-select')
        elif isinstance(w, forms.CheckboxInput):
            w.attrs.setdefault('class', 'form-check-input')
        elif isinstance(w, forms.Textarea):
            w.attrs.setdefault('class', 'form-control')
        else:
            w.attrs.setdefault('class', 'form-control')


def _decimales_sin_confusion_local(form, *nombres_campos):
    """
    Evita que formatos regionales interpreten mal montos (p. ej. 1.210 como 1,21).
    Usa punto decimal y entrada numérica HTML5.
    """
    for nombre in nombres_campos:
        f = form.fields.get(nombre)
        if not f:
            continue
        f.localize = False
        f.widget = forms.NumberInput(
            attrs={
                'step': '0.01',
                'min': '0',
                'class': 'form-control',
                'placeholder': '0.00',
            }
        )


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        _decimales_sin_confusion_local(self, 'precio')

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'precio',
            'talla',
            'estado',
            'stock_producto',
            'descripcion',
            'id_tipo_cierre',
            'id_marca',
            'id_color',
            'id_genero',
            'id_categoria',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class UsuarioAdminForm(forms.ModelForm):
    clave_nueva = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Dejar en blanco para no cambiar la contraseña al editar.',
    )

    def __init__(self, *args, creating=False, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        if creating:
            self.fields['clave_nueva'].required = True
            self.fields['clave_nueva'].help_text = 'Obligatoria para el nuevo usuario.'

    class Meta:
        model = Usuario
        fields = [
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'direccion',
            'contacto',
            'gmail',
            'id_rol',
        ]

    def save(self, commit=True):
        inst = super().save(commit=False)
        pwd = self.cleaned_data.get('clave_nueva')
        if pwd:
            inst.clave = make_password(pwd)
        if commit:
            inst.save()
        return inst


class MarcaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)

    class Meta:
        model = marcas
        fields = ['nombre_marca']


class ColorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)

    class Meta:
        model = colores
        fields = ['nombre_color']


class CategoriaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)

    class Meta:
        model = categoria
        fields = ['nombre_categoria']


class GeneroForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)

    class Meta:
        model = genero
        fields = ['nombre_genero']


class TipoCierreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)

    class Meta:
        model = tipos_cierres
        fields = ['tipo_cierre']


ESTADOS_VENTA = [
    ('', 'Seleccione estado'),
    ('pendiente', 'Pendiente'),
    ('pagado', 'Pagado'),
    ('cancelado', 'Cancelado'),
    ('entregado', 'Entregado'),
]

ESTADOS_PAGO = [
    ('', 'Seleccione estado'),
    ('pendiente', 'Pendiente'),
    ('completado', 'Completado'),
    ('rechazado', 'Rechazado'),
]

METODOS_PAGO = [
    ('', 'Seleccione método'),
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
    ('transferencia', 'Transferencia'),
]

OPCIONES_PAGO = [
    ('', 'Seleccione opción'),
    ('contado', 'Contado'),
    ('credito', 'Crédito'),
    ('debito', 'Débito'),
]


class VentaForm(forms.ModelForm):
    estado_venta = forms.ChoiceField(
        choices=[x for x in ESTADOS_VENTA if x[0]],
        initial='pendiente',
    )
    producto_inicial = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        label='Producto',
        help_text='Opcional: crea una línea de detalle al guardar.',
    )
    cantidad_inicial = forms.IntegerField(
        required=False,
        min_value=1,
        label='Cantidad',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        _decimales_sin_confusion_local(self, 'total')
        self.fields['fecha_ventas'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        )
        self.fields['fecha_ventas'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['total'].label = 'Total de la venta'
        self.fields['total'].help_text = 'Monto total de esta venta (use punto para decimales: 1210.50).'

    class Meta:
        model = Venta
        fields = ['fecha_ventas', 'estado_venta', 'total', 'id_usuario']
        labels = {
            'id_usuario': 'Usuario',
            'fecha_ventas': 'Fecha',
        }

    def clean(self):
        data = super().clean()
        prod = data.get('producto_inicial')
        cant = data.get('cantidad_inicial')
        if bool(prod) != bool(cant):
            raise ValidationError('Si indica producto o cantidad, debe completar ambos campos.')
        return data


class VentaEditForm(forms.ModelForm):
    estado_venta = forms.ChoiceField(choices=[x for x in ESTADOS_VENTA if x[0]])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        _decimales_sin_confusion_local(self, 'total')
        self.fields['fecha_ventas'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        )
        self.fields['fecha_ventas'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['total'].label = 'Total de la venta'
        self.fields['total'].help_text = 'Monto total (punto decimal: 1210.50).'

    class Meta:
        model = Venta
        fields = ['fecha_ventas', 'estado_venta', 'total', 'id_usuario']
        labels = {'id_usuario': 'Usuario', 'fecha_ventas': 'Fecha'}


class PagoForm(forms.ModelForm):
    estado_pago = forms.ChoiceField(choices=[x for x in ESTADOS_PAGO if x[0]])
    metodo_pagos = forms.ChoiceField(choices=[x for x in METODOS_PAGO if x[0]])
    opcion_pagos = forms.ChoiceField(choices=[x for x in OPCIONES_PAGO if x[0]])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        _decimales_sin_confusion_local(self, 'precio')
        qs = Venta.objects.all().order_by('-id_ventas')
        self.fields['id_venta'].queryset = qs
        self.fields['id_venta'].label = 'Venta asociada (opcional)'
        self.fields['id_venta'].required = False
        self.fields['id_venta'].empty_label = 'Sin venta (N/A)'
        self.fields['id_venta'].help_text = (
            'Solo enlaza el pago con una venta; el total de la venta se muestra como referencia, '
            'no sustituye al monto del pago.'
        )
        self.fields['precio'].label = 'Monto de este pago'
        self.fields['precio'].help_text = 'Lo que se cobra en este pago (punto decimal: 50000.00). No es el total de la venta.'

        def _label_venta(v):
            return f'#{v.id_ventas} — total venta ${v.total}'

        self.fields['id_venta'].label_from_instance = _label_venta

    class Meta:
        model = Pago
        fields = ['precio', 'estado_pago', 'metodo_pagos', 'opcion_pagos', 'id_venta']
        labels = {
            'precio': 'Monto del pago',
            'estado_pago': 'Estado del pago',
            'metodo_pagos': 'Método de pago',
            'opcion_pagos': 'Opción de pago',
        }


class PersonalizacionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplicar_estilos_bootstrap(self)
        self.fields['fecha_solicitud'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        self.fields['descripcion'].widget = forms.Textarea(attrs={'rows': 4})

    class Meta:
        model = Personalizacion
        fields = [
            'descripcion',
            'imagen_personalizacion',
            'fecha_solicitud',
            'id_usuario',
            'id_categoria',
            'id_color',
            'id_marca',
            'id_genero',
        ]
        labels = {
            'id_usuario': 'Cliente',
            'id_categoria': 'Categoría',
            'id_color': 'Color',
            'id_marca': 'Marca',
            'id_genero': 'Género',
            'imagen_personalizacion': 'Imagen',
        }
