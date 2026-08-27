from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.models import Usuario
from reservas.models import Reserva
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .decorador import solo_anonimos, verificar, solo_admin


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


