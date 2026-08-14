from django.shortcuts import render, redirect
from django.contrib import messages
from usuarios.models import Usuario
from usuarios.serializador import UsuarioSerializer
from .serializador import *
from rest_framework import viewsets

def inicio_sesion(request):
    if request.method == "POST":
        # Creamos una variable que atrapa lo que viene en el HTML
        usuario_html = request.POST.get("usuario").strip().lower()
        clave_html = request.POST.get("contraseña")

        try:
            # Acá hacemos un query para ver si coincide con la BD
            q = Usuario.objects.get(usuario=usuario_html, contraseña=clave_html)

            # CONTROL DE SEGURIDAD: Validamos si la cuenta está suspendida antes de dejarlo entrar
            if "[SUSPENDIDO]" in q.nombre:
                messages.error(request, "Tu cuenta se encuentra suspendida. Comunícate con el administrador.")
                return redirect('iniciar_sesion')  # O como se llame la URL de tu login
            # Guardamos la manilla en el maletín (Sesión)
            request.session["logueado"] = {
                "id": q.id,
                "nombre": q.nombre,
                "rol": q.rol,
            }

            return redirect('inicio')

        except Usuario.DoesNotExist:
            request.session["logueado"] = None
            messages.error(request, "Usuario o contraseña incorrectos")
            return redirect('iniciar_sesion')

    return render(request, "login.html")

def logout(request):
    try:
        del request.session["logueado"]
        messages.success(request, "¡Sesión cerrada con éxito, vuelve pronto!")
        return redirect('inicio')
    except Exception as e:
        return redirect('inicio')


def crear_usuario(request):
    if request.method == "POST":
        # Obtenemos los datos del formulario
        usuario = request.POST.get("usuario").strip()
        nombre = request.POST.get("nombre").strip().title()
        apellido = request.POST.get("apellido").strip().title()
        email = request.POST.get("email").strip().lower()
        contraseña = request.POST.get("contraseña").strip()

    

        
        Usuario.objects.create(
            usuario=usuario,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=contraseña,
        )
        return redirect('iniciar_sesion')

    # Arreglado: Limpiamos el error de sintaxis que se mezcló aquí abajo
    return render(request, "register.html")


def mostrar_usuarios(request):
    t_usuarios = Usuario.objects.all()
    contexto = {
        'usuarios' : t_usuarios
    }
    return render(request, "listado_general.html",contexto)


# 1. LA VISTA PARA VER LOS PERFILES (Cortica y limpia)
def perfiles_clientes(request):
    # Traemos todos los usuarios que son clientes y todas las reservas
    todos_los_clientes = Usuario.objects.filter(rol='cliente')
    todas_las_reservas = Reserva.objects.all()

    contexto = {
        'clientes': todos_los_clientes,
        'reservas': todas_las_reservas
    }
    return render(request, 'admin/perfiles_cliente.html', contexto)


# 2. LA VISTA PARA SUSPENDER (Un truco simple con el nombre)
def cambiar_estado_usuario(request, usuario_id):
    usuario = Usuario.objects.get(id=usuario_id)

    # Si no está suspendido, le añadimos la palabra [SUSPENDIDO] al nombre
    if "[SUSPENDIDO]" not in usuario.nombre:
        usuario.nombre = f"{usuario.nombre} [SUSPENDIDO]"
        messages.success(request, f"Usuario suspendido con éxito.")
    else:
        # Si ya estaba suspendido, le quitamos la palabra para reactivarlo
        usuario.nombre = usuario.nombre.replace(" [SUSPENDIDO]", "")
        messages.success(request, f"Usuario reactivado con éxito.")

    usuario.save()
    return redirect('listado_general')


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

