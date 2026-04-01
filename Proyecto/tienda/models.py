import hashlib

from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.db import models


def es_hash_django(encoded):
    """True si el valor es un hash reconocido por Django (pbkdf2, argon2, bcrypt, etc.)."""
    if not encoded or not isinstance(encoded, str):
        return False
    try:
        identify_hasher(encoded)
        return True
    except ValueError:
        return False


class Rol (models.Model):
   id_rol = models.AutoField(primary_key=True)
   nombre_rol = models.CharField(max_length=50)
   
   class Meta:
       db_table = 'roles'

   def __str__(self):
       return self.nombre_rol


class Usuario (models.Model):
    id_usuario = models.AutoField(primary_key=True)
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100)
    contacto = models.CharField(max_length=20)
    gmail = models.EmailField(max_length=100)
    clave = models.CharField(max_length=255)
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='id_rol')
    
    class Meta:
        db_table = 'usuarios'
    
    def save(self, *args, **kwargs):
        # Solo hashear si aún no es un hash Django (evita doble hash y soporta argon2, etc.)
        if self.clave and not es_hash_django(self.clave):
            self.clave = make_password(self.clave)
        super().save(*args, **kwargs)

    def verificar_clave(self, raw_password):
        """
        Comprueba la contraseña: hash Django, texto plano (datos legacy) o MD5 (32 hex, típico de apps Java).
        """
        if raw_password is None or self.clave is None:
            return False
        raw_password = raw_password if isinstance(raw_password, str) else str(raw_password)
        stored = self.clave.strip() if isinstance(self.clave, str) else ''

        if es_hash_django(stored):
            return check_password(raw_password, stored)

        # Texto plano (misma cadena que en BD)
        if raw_password == stored:
            return True

        # MD5 en hexadecimal (32 caracteres)
        if len(stored) == 32:
            try:
                digest = hashlib.md5(raw_password.encode('utf-8')).hexdigest()
                if digest.lower() == stored.lower():
                    return True
            except Exception:
                pass

        return False

    def migrar_clave_a_hash_django(self, raw_password):
        """Tras login correcto con formato legacy, guarda pbkdf2 para los próximos accesos."""
        if not raw_password or es_hash_django(self.clave):
            return
        self.clave = make_password(raw_password)
        self.save(update_fields=['clave'])

    def __str__(self):
        return f'{self.primer_nombre} {self.primer_apellido} ({self.gmail})'


class tipos_cierres (models.Model):
    id_tipo_cierre = models.AutoField(primary_key=True)
    tipo_cierre = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'tipos_cierres'

    def __str__(self):
        return self.tipo_cierre


class marcas (models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre_marca = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'marcas'

    def __str__(self):
        return self.nombre_marca
        
class colores (models.Model):
    id_color = models.AutoField(primary_key=True)
    nombre_color = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'colores'

    def __str__(self):
        return self.nombre_color

class genero (models.Model):
    id_genero = models.AutoField(primary_key=True)
    nombre_genero = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'generos'

    def __str__(self):
        return self.nombre_genero


class categoria (models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre_categoria

class Producto (models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    talla = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, db_column='imagen')
    estado = models.CharField(max_length=20)
    stock_producto = models.IntegerField()
    descripcion = models.TextField()
    id_tipo_cierre = models.ForeignKey(tipos_cierres, on_delete=models.CASCADE, db_column='id_tipo_cierre')
    id_marca = models.ForeignKey(marcas, on_delete=models.CASCADE, db_column='id_marca')
    id_color = models.ForeignKey(colores, on_delete=models.CASCADE, db_column='id_color')
    id_genero = models.ForeignKey(genero, on_delete=models.CASCADE, db_column='id_genero')    
    id_categoria = models.ForeignKey(categoria, on_delete=models.CASCADE, db_column='id_categoria')
    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    id_ventas = models.AutoField(primary_key=True)
    fecha_ventas = models.DateField()
    estado_venta = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=12, decimal_places=2, db_column='Total')
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='ventas'
    )

    class Meta:
        db_table = 'ventas'
        ordering = ['-id_ventas']

    def __str__(self):
        return f'Venta #{self.id_ventas}'

    def productos_resumen(self):
        detalles = self.detalles.select_related('id_producto').all()
        if not detalles:
            return 'N/A'
        parts = []
        for d in detalles:
            nombre = d.id_producto.nombre if d.id_producto_id else 'N/A'
            parts.append(f'{nombre} (x{d.cantidad})')
        return ', '.join(parts)

    def cantidad_productos_total(self):
        s = sum(d.cantidad for d in self.detalles.all())
        return s if s > 0 else 1


class DetalleVenta(models.Model):
    id_detalle_venta = models.AutoField(primary_key=True)
    cantidad = models.IntegerField()
    cantidad_pagada = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    id_venta = models.ForeignKey(
        Venta, on_delete=models.CASCADE, db_column='id_venta', related_name='detalles'
    )
    id_producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, db_column='id_producto'
    )

    class Meta:
        db_table = 'detalles_ventas'


class Pago(models.Model):
    id_pagos = models.AutoField(primary_key=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    estado_pago = models.CharField(max_length=50)
    metodo_pagos = models.CharField(max_length=50)
    opcion_pagos = models.CharField(max_length=50, blank=True)
    id_venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        db_column='id_venta',
        null=True,
        blank=True,
        related_name='pagos',
    )

    class Meta:
        db_table = 'pagos'
        ordering = ['-id_pagos']

    def __str__(self):
        return f'Pago #{self.id_pagos}'


class Valoracion(models.Model):
    id_valoracion = models.AutoField(primary_key=True)
    valor_puntuacion = models.IntegerField()
    fecha_puntuacion = models.DateField(auto_now_add=True)
    comentario = models.TextField(blank=True)
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='valoraciones',
    )
    id_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        db_column='id_producto',
        related_name='valoraciones',
    )

    class Meta:
        db_table = 'valoraciones'
        ordering = ['-fecha_puntuacion']
        managed = False

    def __str__(self):
        return f'Valoración #{self.id_valoracion} para {self.id_producto.nombre}'


class Personalizacion(models.Model):
    id_personalizacion = models.AutoField(primary_key=True)
    descripcion = models.TextField(blank=True)
    imagen_personalizacion = models.ImageField(
        upload_to='personalizaciones/', blank=True, null=True
    )
    fecha_solicitud = models.DateField()
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, db_column='id_usuario', related_name='personalizaciones'
    )
    id_categoria = models.ForeignKey(
        categoria, on_delete=models.CASCADE, db_column='id_categoria'
    )
    id_color = models.ForeignKey(colores, on_delete=models.CASCADE, db_column='id_color')
    id_marca = models.ForeignKey(marcas, on_delete=models.CASCADE, db_column='id_marca')
    id_genero = models.ForeignKey(genero, on_delete=models.CASCADE, db_column='id_genero')

    class Meta:
        db_table = 'personalizacion'
        ordering = ['-id_personalizacion']

    def __str__(self):
        return f'Personalización #{self.id_personalizacion}'

    def nombre_usuario_completo(self):
        u = self.id_usuario
        return f'{u.primer_nombre} {u.primer_apellido}'.strip()

