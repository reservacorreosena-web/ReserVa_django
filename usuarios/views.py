from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
import json

from usuarios.models import Usuario
from reservas.models import Reserva
from .decorador import solo_anonimos, verificar, solo_admin
from usuarios.serializador import UsuarioSerializer
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


@csrf_exempt
@require_http_methods(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        data = request.POST

    email = (data.get('email') or data.get('username') or data.get('correo') or '').strip().lower()
    password = data.get('password') or data.get('contraseña') or data.get('clave') or ''

    if not email or not password:
        return JsonResponse({'detail': 'Email y contraseña son obligatorios.'}, status=400)

    try:
        usuario_app = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'detail': 'Credenciales inválidas.'}, status=401)

    clave_valida = check_password(password, usuario_app.contraseña)
    if not clave_valida and usuario_app.contraseña == password:
        clave_valida = True
        usuario_app.contraseña = make_password(password)
        usuario_app.save(update_fields=['contraseña'])

    if not clave_valida:
        return JsonResponse({'detail': 'Credenciales inválidas.'}, status=401)

    if "[SUSPENDIDO]" in (usuario_app.nombre or ''):
        return JsonResponse({'detail': 'Tu cuenta se encuentra suspendida.'}, status=403)

    auth_user, _ = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': usuario_app.nombre or ''}
    )
    if not auth_user.email:
        auth_user.email = email
        auth_user.save(update_fields=['email'])

    token, _ = Token.objects.get_or_create(user=auth_user)

    return JsonResponse({
        'token': token.key,
        'user': {
            'id': usuario_app.id,
            'nombre': usuario_app.nombre,
            'email': usuario_app.email,
            'rol': usuario_app.rol,
            'estado': usuario_app.estado,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    email = getattr(request.user, 'email', '') or request.user.username
    usuario_app = Usuario.objects.filter(email=email).first()
    if not usuario_app:
        return JsonResponse({
            'user': {
                'username': request.user.username,
                'email': request.user.email,
            }
        })
    return JsonResponse({
        'user': {
            'id': usuario_app.id,
            'nombre': usuario_app.nombre,
            'email': usuario_app.email,
            'rol': usuario_app.rol,
            'estado': usuario_app.estado,
        }
    })


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