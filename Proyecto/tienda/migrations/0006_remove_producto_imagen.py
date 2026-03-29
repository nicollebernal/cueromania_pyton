"""Quita el campo imagen de productos en el estado de Django y la columna en la BD si existe."""

from django.db import migrations


def drop_imagen_si_existe(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    with connection.cursor() as cursor:
        if vendor == 'mysql':
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'productos'
                  AND COLUMN_NAME = 'imagen'
                """
            )
            if cursor.fetchone()[0] > 0:
                cursor.execute('ALTER TABLE productos DROP COLUMN imagen')
        elif vendor == 'sqlite':
            cursor.execute('PRAGMA table_info(productos)')
            cols = [row[1] for row in cursor.fetchall()]
            if 'imagen' in cols:
                cursor.execute('ALTER TABLE productos DROP COLUMN imagen')
        elif vendor == 'postgresql':
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'productos'
                  AND column_name = 'imagen'
                """
            )
            if cursor.fetchone()[0] > 0:
                cursor.execute('ALTER TABLE productos DROP COLUMN imagen')


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0005_producto_imagen_si_falta'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='producto',
                    name='imagen',
                ),
            ],
            database_operations=[
                migrations.RunPython(drop_imagen_si_existe, migrations.RunPython.noop),
            ],
        ),
    ]
