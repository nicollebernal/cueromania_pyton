from functools import wraps

from django.shortcuts import redirect

from tienda.models import Usuario


def solo_administrador(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        uid = request.session.get('usuario_id')
        if not uid:
            return redirect('login')
        usuario = (
            Usuario.objects.filter(id_usuario=uid)
            .select_related('id_rol')
            .first()
        )
        if not usuario or not usuario.id_rol:
            return redirect('login')
        if usuario.id_rol.nombre_rol.lower() != 'administrador':
            return redirect('login')
        request.admin_usuario = usuario
        return view_func(request, *args, **kwargs)

    return _wrapped
