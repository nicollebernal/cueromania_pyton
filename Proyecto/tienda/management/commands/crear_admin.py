"""
Crea (o actualiza la contraseña de) un usuario con rol administrador para el panel.

Uso:
  python manage.py crear_admin
  python manage.py crear_admin --email mi@correo.com --password MiClaveSegura
"""

from django.core.management.base import BaseCommand

from tienda.models import Rol, Usuario


class Command(BaseCommand):
    help = 'Crea un usuario administrador para acceder a /administrador/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            default='admin@cueromania.com',
            help='Correo para iniciar sesión (login usa el campo gmail).',
        )
        parser.add_argument(
            '--password',
            default='Cueromania2026!',
            help='Contraseña en texto plano (se guarda hasheada).',
        )

    def handle(self, *args, **options):
        email = (options['email'] or '').strip().lower()
        password = options['password'] or ''

        if not email or not password:
            self.stderr.write(self.style.ERROR('Email y contraseña son obligatorios.'))
            return

        rol = Rol.objects.filter(nombre_rol__iexact='administrador').first()
        if not rol:
            rol = Rol.objects.create(nombre_rol='administrador')

        usuario = Usuario.objects.filter(gmail__iexact=email).first()
        if usuario:
            usuario.id_rol = rol
            usuario.clave = password
            usuario.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuario actualizado: {email} (rol administrador). Ya puede iniciar sesión.'
                )
            )
            return

        Usuario.objects.create(
            primer_nombre='Admin',
            segundo_nombre='',
            primer_apellido='Sistema',
            segundo_apellido='',
            direccion='N/A',
            contacto='0000000000',
            gmail=email,
            clave=password,
            id_rol=rol,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Usuario administrador creado.\n'
                f'  Correo (gmail): {email}\n'
                f'  Contraseña: (la indicada con --password)\n'
                f'Entre en la página de login y use esos datos; será redirigido al panel.'
            )
        )
