from django.shortcuts import redirect
from django.contrib import messages

def verificar(func):
    def vigilante(request, *args, **kwargs):
        if not request.session.get("logueado", False):
            return redirect ('inicio')
        return func(request, *args, **kwargs)
    return vigilante


def solo_anonimos(func):
    def vigilante(request, *args, **kwargs):
        # Si ya tiene la sesión activa, no lo dejamos entrar al Login o Registro
        if request.session.get("logueado", False):
            return redirect('inicio')

        return func(request, *args, **kwargs)

    return vigilante


def solo_admin(func):
    def vigilante(request, *args, **kwargs):
        sesion = request.session.get("logueado", None)

        # Si no hay sesión o el rol no es 'admin'
        if not sesion or sesion.get("rol") != "admin":
            messages.error(request, "Acceso denegado: Se requieren permisos de administrador.")
            return redirect('inicio')

        return func(request, *args, **kwargs)

    return vigilante