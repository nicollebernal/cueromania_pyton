# Si la BD existía sin ejecutar 0002 o la columna no se creó, añade imagen de forma segura.
# Tras 0006 el campo imagen se elimina del modelo; esta migración puede ser no-op si la columna ya no existe.

from django.db import migrations


def add_imagen_si_falta(apps, schema_editor):
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
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'ALTER TABLE productos ADD COLUMN imagen VARCHAR(100) NULL'
                )
        elif vendor == 'sqlite':
            cursor.execute('PRAGMA table_info(productos)')
            cols = [row[1] for row in cursor.fetchall()]
            if 'imagen' not in cols:
                cursor.execute(
                    'ALTER TABLE productos ADD COLUMN imagen VARCHAR(100) NULL'
                )
        elif vendor == 'postgresql':
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'productos'
                  AND column_name = 'imagen'
                """
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'ALTER TABLE productos ADD COLUMN imagen VARCHAR(100) NULL'
                )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0004_usuario_clave_longer'),
    ]

    operations = [
        migrations.RunPython(add_imagen_si_falta, noop_reverse),
    ]
