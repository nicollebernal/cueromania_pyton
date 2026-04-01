from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0007_venta_fecha_solo_date'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                SET @max_ventas := IFNULL((SELECT MAX(id_ventas) FROM ventas WHERE id_ventas <> 0), 0);
                UPDATE ventas
                SET id_ventas = (@max_ventas := @max_ventas + 1)
                WHERE id_ventas = 0
                ORDER BY fecha_ventas, Total;

                SET @max_pagos := IFNULL((SELECT MAX(id_pagos) FROM pagos WHERE id_pagos <> 0), 0);
                UPDATE pagos
                SET id_pagos = (@max_pagos := @max_pagos + 1)
                WHERE id_pagos = 0;

                ALTER TABLE ventas
                    MODIFY id_ventas int(11) NOT NULL AUTO_INCREMENT,
                    ADD PRIMARY KEY (id_ventas);

                ALTER TABLE pagos
                    MODIFY id_pagos int(11) NOT NULL AUTO_INCREMENT,
                    ADD PRIMARY KEY (id_pagos);

                ALTER TABLE detalles_ventas
                    MODIFY id_detalle_venta int(11) NOT NULL AUTO_INCREMENT;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
