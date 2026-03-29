from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0006_remove_producto_imagen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venta',
            name='fecha_ventas',
            field=models.DateField(),
        ),
    ]
