from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.models import Usuario

from reservas.models import Reserva
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .decorador import solo_anonimos, verificar, solo_admin

from usuarios.serializador import UsuarioSerializer
from .serializador import *
from rest_framework import viewsets



@solo_anonimos
def inicio_sesion(request):
    if request.method == "POST":
        # Usamos .get() y validamos por si llega nulo antes de aplicar .strip()
        email_raw = request.POST.get("email")
        clave_html = request.POST.get("contraseña")

        if not email_raw or not clave_html:
            messages.error(request, "Por favor completa todos los campos.")
            return redirect('iniciar_sesion')

        email_html = email_raw.strip().lower()

        try:
            q = Usuario.objects.get(email=email_html, contraseña=clave_html)

            if "[SUSPENDIDO]" in q.nombre:
                messages.error(request, "Tu cuenta se encuentra suspendida. Comunícate con el administrador.")
                return redirect('iniciar_sesion')

            request.session["logueado"] = {
                "id": q.id,
                "nombre": q.nombre,
                "rol": q.rol,
            }

            return redirect('inicio')

        except Usuario.DoesNotExist:
            request.session["logueado"] = None
            messages.error(request, "Correo o contraseña incorrectos")
            return redirect('iniciar_sesion')

    return render(request, "login.html")

def logout(request):
    try:
        del request.session["logueado"]
        messages.success(request, "¡Sesión cerrada con éxito, vuelve pronto!")
        return redirect('inicio')
    except Exception as e:
        return redirect('inicio')


@solo_anonimos
def crear_usuario(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip().title()
        email = request.POST.get("email").strip().lower()
        contraseña = request.POST.get("contraseña").strip()

        # Diccionario para conservar lo que escribió el usuario si hay un error
        datos_form = {'nombre': nombre, 'email': email}

        if len(contraseña) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, "register.html", {'datos_form': datos_form})

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Este correo ya se encuentra registrado.")
            return render(request, "register.html", {'datos_form': datos_form})

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Ingrese un correo válido.")
            return render(request, "register.html", {'datos_form': datos_form})

        Usuario.objects.create(
            nombre=nombre,
            email=email,
            contraseña=contraseña,
            rol='cliente'
        )
        messages.success(request, "¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
        return redirect('iniciar_sesion')

    return render(request, "register.html")

@solo_admin
def mostrar_usuarios(request):
    t_usuarios = Usuario.objects.all()
    contexto = {
        'usuarios' : t_usuarios
    }
    return render(request, "listado_general.html",contexto)

@solo_admin
def perfiles_clientes(request):
    # Traemos todos los usuarios que son clientes y todas las reservas
    todos_los_clientes = Usuario.objects.filter(rol='cliente')
    todas_las_reservas = Reserva.objects.all()

    contexto = {
        'clientes': todos_los_clientes,
        'reservas': todas_las_reservas
    }
    return render(request, 'admin/perfiles_cliente.html', contexto)


@solo_admin
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if "[SUSPENDIDO]" not in usuario.nombre:
        usuario.nombre = f"{usuario.nombre} [SUSPENDIDO]"
        messages.success(request, "Usuario suspendido con éxito.")
    else:
        usuario.nombre = usuario.nombre.replace(" [SUSPENDIDO]", "")
        messages.success(request, "Usuario reactivado con éxito.")

    usuario.save()
    return redirect('listado_general')


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

def editar_perfil(request):
    # Verificamos que el usuario esté logueado en la sesión
    usuario_sesion = request.session.get("logueado")
    if not usuario_sesion:
        messages.error(request, "Debes iniciar sesión para editar tu perfil.")
        return redirect('iniciar_sesion')

    # Buscamos al usuario en la base de datos usando el ID de la sesión
    usuario = get_object_or_404(Usuario, id=usuario_sesion["id"])

    if request.method == "POST":
        # Capturamos los datos enviados por el formulario
        nuevo_nombre = request.POST.get("nombre", "").strip().title()
        nuevo_email = request.POST.get("email", "").strip().lower()
        nueva_contraseña = request.POST.get("contraseña", "").strip()

        # Validar campos obligatorios
        if not nuevo_nombre or not nuevo_email:
            messages.error(request, "El nombre y el correo son obligatorios.")
            return render(request, "editar_perfil.html", {"usuario": usuario})

        # Validar que el correo no esté registrado por otra cuenta distinta
        if Usuario.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
            messages.error(request, "Este correo ya está registrado por otra cuenta.")
            return render(request, "editar_perfil.html", {"usuario": usuario})

        # Validar formato de correo electrónico
        try:
            validate_email(nuevo_email)
        except ValidationError:
            messages.error(request, "Ingrese un correo electrónico válido.")
            return render(request, "editar_perfil.html", {"usuario": usuario})

        # Asignar los nuevos valores básicos
        usuario.nombre = nuevo_nombre
        usuario.email = nuevo_email

        # Validación y actualización de la contraseña (opcional)
        if nueva_contraseña:
            if len(nueva_contraseña) < 8:
                messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
                return render(request, "editar_perfil.html", {"usuario": usuario})
            usuario.contraseña = nueva_contraseña

        # Guardar cambios en la base de datos
        usuario.save()

        # Actualizar el nombre en la sesión actual para que refleje el cambio arriba en el navbar/perfil
        request.session["logueado"]["nombre"] = usuario.nombre

        messages.success(request, "¡Tus datos han sido actualizados con éxito!")
        return redirect('editar_perfil')

    return render(request, "editar_perfil.html", {"usuario": usuario})