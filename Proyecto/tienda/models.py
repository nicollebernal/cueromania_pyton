from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Rol (models.Model):
   id_rol = models.AutoField(primary_key=True)
   nombre_rol = models.CharField(max_length=50)
   
   class Meta:
       db_table = 'roles'


class Usuario (models.Model):
    id_usuario = models.AutoField(primary_key=True)
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100)
    contacto = models.CharField(max_length=20)
    gmail = models.EmailField(max_length=100)
    clave = models.CharField(max_length=100)
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='id_rol')
    
    class Meta:
        db_table = 'usuarios'
    
    def save(self, *args, **kwargs ):
        if not self.clave.startswith('pbkdf2_'):
            self.clave = make_password(self.clave)
        super().save(*args, **kwargs)
    def verificar_clave(self,password):
        return check_password(password, self.clave)


class tipos_cierres (models.Model):
    id_tipo_cierre = models.AutoField(primary_key=True)
    tipo_cierre = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'tipos_cierres'


class marcas (models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre_marca = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'marcas'
        
class colores (models.Model):
    id_color = models.AutoField(primary_key=True)
    nombre_color = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'colores'

class genero (models.Model):
    id_genero = models.AutoField(primary_key=True)
    nombre_genero = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'generos'


class categoria (models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'categorias'

class Producto (models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    talla = models.CharField(max_length=20)
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

