from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0003_venta_detalleventa_pago_personalizacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='clave',
            field=models.CharField(max_length=255),
        ),
    ]
