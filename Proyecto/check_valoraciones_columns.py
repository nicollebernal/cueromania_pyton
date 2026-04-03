import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cueromania.settings')

django.setup()
from django.db import connection
with connection.cursor() as c:
    c.execute('SHOW COLUMNS FROM valoraciones')
    cols = c.fetchall()
print('valoraciones columns:', cols)
