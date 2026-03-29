# Generated manually for parity with JSF / MySQL schema

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0002_producto_imagen'),
    ]

    operations = [
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id_ventas', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_ventas', models.DateTimeField()),
                ('estado_venta', models.CharField(max_length=50)),
                ('total', models.DecimalField(db_column='Total', decimal_places=2, max_digits=12)),
                ('id_usuario', models.ForeignKey(db_column='id_usuario', on_delete=django.db.models.deletion.CASCADE, related_name='ventas', to='tienda.usuario')),
            ],
            options={
                'db_table': 'ventas',
                'ordering': ['-id_ventas'],
            },
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id_pagos', models.AutoField(primary_key=True, serialize=False)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado_pago', models.CharField(max_length=50)),
                ('metodo_pagos', models.CharField(max_length=50)),
                ('opcion_pagos', models.CharField(blank=True, max_length=50)),
                ('id_venta', models.ForeignKey(blank=True, db_column='id_venta', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pagos', to='tienda.venta')),
            ],
            options={
                'db_table': 'pagos',
                'ordering': ['-id_pagos'],
            },
        ),
        migrations.CreateModel(
            name='DetalleVenta',
            fields=[
                ('id_detalle_venta', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('cantidad_pagada', models.DecimalField(decimal_places=2, max_digits=12)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('id_producto', models.ForeignKey(db_column='id_producto', on_delete=django.db.models.deletion.CASCADE, to='tienda.producto')),
                ('id_venta', models.ForeignKey(db_column='id_venta', on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='tienda.venta')),
            ],
            options={
                'db_table': 'detalles_ventas',
            },
        ),
        migrations.CreateModel(
            name='Personalizacion',
            fields=[
                ('id_personalizacion', models.AutoField(primary_key=True, serialize=False)),
                ('descripcion', models.TextField(blank=True)),
                ('imagen_personalizacion', models.ImageField(blank=True, null=True, upload_to='personalizaciones/')),
                ('fecha_solicitud', models.DateField()),
                ('id_categoria', models.ForeignKey(db_column='id_categoria', on_delete=django.db.models.deletion.CASCADE, to='tienda.categoria')),
                ('id_color', models.ForeignKey(db_column='id_color', on_delete=django.db.models.deletion.CASCADE, to='tienda.colores')),
                ('id_genero', models.ForeignKey(db_column='id_genero', on_delete=django.db.models.deletion.CASCADE, to='tienda.genero')),
                ('id_marca', models.ForeignKey(db_column='id_marca', on_delete=django.db.models.deletion.CASCADE, to='tienda.marcas')),
                ('id_usuario', models.ForeignKey(db_column='id_usuario', on_delete=django.db.models.deletion.CASCADE, related_name='personalizaciones', to='tienda.usuario')),
            ],
            options={
                'db_table': 'personalizacion',
                'ordering': ['-id_personalizacion'],
            },
        ),
    ]
