from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from usuarios.models import Usuario
from reservas.models import Reserva
from .decorador import solo_anonimos, verificar, solo_admin
from usuarios.serializador import (
    AuthResponseSerializer,
    LoginSerializer,
    MeResponseSerializer,
    RegistroSerializer,
    UsuarioSerializer,
)
from .serializador import *

# Importaciones para la recuperación de contraseña personalizada
from .utils import enviar_correo_recuperacion, generar_token_personalizado
from django.utils.http import urlsafe_base64_decode


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
            q = Usuario.objects.get(email=email_html)

            # Verificación de contraseña: hash seguro o migración transparente si estaba en texto plano
            clave_valida = check_password(clave_html, q.contraseña)
            if not clave_valida and q.contraseña == clave_html:
                clave_valida = True
                q.contraseña = make_password(clave_html)
                q.save(update_fields=['contraseña'])

            if not clave_valida:
                raise Usuario.DoesNotExist

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
            contraseña=make_password(contraseña),
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
@require_POST
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    # Bloquear suspensión de usuarios con rol de Administrador
    if usuario.rol == 'admin' and "[SUSPENDIDO]" not in usuario.nombre:
        messages.error(request, "No se puede suspender a un usuario con rol de Administrador.")
        return redirect('listado_general')

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
    permission_classes = [IsAuthenticated]


def _datos_usuario(usuario_app):
    return {
        "id": usuario_app.id,
        "nombre": usuario_app.nombre,
        "email": usuario_app.email,
        "rol": usuario_app.rol,
        "estado": usuario_app.estado,
    }


def _auth_user_compatible(auth_user, usuario_app):
    """Evita reutilizar una cuenta de Django con privilegios para un cliente.

    El ``auth.User`` solo sirve como titular del token. Un cliente nunca debe
    recibir el token de un ``auth.User`` que sea staff/superusuario o que tenga
    una contraseña propia (por ejemplo, una cuenta creada con
    ``createsuperuser``). Los usuarios de la app creados por la API tienen
    contraseña vacía o inutilizable y sí pueden reutilizarse.
    """
    if usuario_app.rol == "admin":
        return True
    if auth_user.is_staff or auth_user.is_superuser:
        return False
    if auth_user.password and not auth_user.password.startswith("!"):
        return False
    return True


def _obtener_o_crear_token(usuario_app):
    """Crea/obtiene el auth.User y el token DRF para un Usuario de la app.

    El auth.User se usa solo como titular del token; la contraseña real vive
    hasheada en ``usuarios.Usuario``. Si el auth.User se crea aquí se marca con
    contraseña inutilizable para que no pueda autenticarse por
    ``/api-token-auth/``.
    """
    auth_user, creado = User.objects.get_or_create(
        username=usuario_app.email,
        defaults={
            "email": usuario_app.email,
            "first_name": usuario_app.nombre or "",
        },
    )

    if not _auth_user_compatible(auth_user, usuario_app):
        raise PermissionDenied(
            "Este correo no está disponible para el acceso de clientes."
        )

    campos = []
    if not auth_user.email:
        auth_user.email = usuario_app.email
        campos.append("email")
    if creado:
        auth_user.set_unusable_password()
        campos.append("password")
    if campos:
        auth_user.save(update_fields=campos)

    token, _ = Token.objects.get_or_create(user=auth_user)
    return token


@extend_schema(
    request=LoginSerializer,
    responses={200: AuthResponseSerializer},
    description="Autentica un cliente y devuelve su token DRF.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    data = request.data

    if not hasattr(data, "get"):
        return Response(
            {"detail": "El cuerpo de la petición debe ser un objeto JSON."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = (
        (data.get("email") or data.get("username") or data.get("correo") or "")
        .strip()
        .lower()
    )
    password = data.get("password") or data.get("contraseña") or data.get("clave") or ""

    if not email or not password:
        return Response(
            {"detail": "Email y contraseña son obligatorios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario_app = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    clave_valida = check_password(password, usuario_app.contraseña)
    if not clave_valida and usuario_app.contraseña == password:
        # Migración transparente de contraseñas legadas en texto plano.
        clave_valida = True
        usuario_app.contraseña = make_password(password)
        usuario_app.save(update_fields=["contraseña"])

    if not clave_valida:
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if "[SUSPENDIDO]" in (usuario_app.nombre or ""):
        return Response(
            {"detail": "Tu cuenta se encuentra suspendida."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not usuario_app.estado:
        return Response(
            {"detail": "Tu cuenta se encuentra deshabilitada."},
            status=status.HTTP_403_FORBIDDEN,
        )

    token = _obtener_o_crear_token(usuario_app)

    return Response(
        {
            "token": token.key,
            "user": _datos_usuario(usuario_app),
        }
    )


@extend_schema(
    request=RegistroSerializer,
    responses={201: AuthResponseSerializer},
    description=(
        "Registra un cliente nuevo y devuelve un token para iniciar sesión."
    ),
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """Registro de clientes desde Flutter.

    Crea el ``usuarios.Usuario`` con contraseña hasheada, el ``auth.User``
    titular del token y devuelve el token para iniciar sesión inmediatamente.
    """
    serializer = RegistroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        with transaction.atomic():
            usuario_app = serializer.save()
            token = _obtener_o_crear_token(usuario_app)
    except IntegrityError:
        return Response(
            {"email": ["Este correo ya se encuentra registrado."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "token": token.key,
            "user": _datos_usuario(usuario_app),
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    request=None,
    responses={204: None},
    description="Revoca el token del usuario autenticado.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Revoca el token del usuario autenticado."""
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses={200: MeResponseSerializer},
    description="Devuelve el perfil del usuario autenticado.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_me(request):
    email = getattr(request.user, "email", "") or request.user.username
    usuario_app = Usuario.objects.filter(email=email).first()
    if not usuario_app:
        return Response(
            {
                "user": {
                    "username": request.user.username,
                    "email": request.user.email,
                }
            }
        )
    return Response({"user": _datos_usuario(usuario_app)})



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
            usuario.contraseña = make_password(nueva_contraseña)

        # Guardar cambios en la base de datos
        usuario.save()

        # Actualizar el nombre en la sesión actual para que refleje el cambio arriba en el navbar/perfil
        request.session["logueado"]["nombre"] = usuario.nombre

        messages.success(request, "¡Tus datos han sido actualizados con éxito!")
        return redirect('editar_perfil')

    return render(request, "editar_perfil.html", {"usuario": usuario})


# ==========================================
# VISTAS DE RECUPERACIÓN DE CONTRASEÑA PERSONALIZADAS
# ==========================================

def recuperar_contrasena_custom(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        try:
            usuario = Usuario.objects.get(email=email)
            enviar_correo_recuperacion(usuario, request)
        except Usuario.DoesNotExist:
            # Por seguridad no revelamos si el correo existe, pero redirigimos al mensaje de enviado
            pass
        
        return redirect("password_reset_done")

    return render(request, "password_reset_form.html")


def password_reset_done_view(request):
    return render(request, "password_reset_done.html")


def reset_confirm_custom(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    # Validamos usando nuestro generador personalizado inmune a campos de Django
    token_valido = generar_token_personalizado(usuario) if usuario else None

    if usuario is not None and token == token_valido:
        if request.method == "POST":
            nueva_password = request.POST.get("password", "").strip()
            if len(nueva_password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
                return render(request, "password_reset_confirm.html")
            
            usuario.contraseña = make_password(nueva_password)
            usuario.save()
            return redirect("password_reset_complete")
        
        return render(request, "password_reset_confirm.html")
    else:
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect("iniciar_sesion")


def password_reset_complete_view(request):
    return render(request, "password_reset_complete.html")