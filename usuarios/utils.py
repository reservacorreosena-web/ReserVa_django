import hashlib
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def generar_token_personalizado(usuario):
    # Creamos un hash único usando datos del usuario
    valor_secreto = f"{usuario.pk}-{usuario.email}-{usuario.contraseña}"
    return hashlib.sha256(valor_secreto.encode()).hexdigest()

def enviar_correo_recuperacion(usuario, request):
    token = generar_token_personalizado(usuario)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    
    link = request.build_absolute_uri(f"/usuarios/reset/{uid}/{token}/")
    
    subject = 'Recuperación de Contraseña - ReserVa'
    to = [usuario.email]
    
    text_content = f"Hola {usuario.nombre}, ingresa al siguiente enlace para restablecer tu contraseña: {link}"
    
    html_content = f"""
        <div style="background-color: #0a0a0a; color: #ffffff; padding: 30px; font-family: Arial, sans-serif; border-radius: 8px;">
            <h2 style="color: #c9a961; font-family: serif;">Reser<span style="color: #ffffff;">Va</span></h2>
            <p>Hola <strong>{usuario.nombre}</strong>, has solicitado restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente botón para continuar:</p>
            <a href="{link}" style="background-color: #c9a961; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 15px;">Restablecer Contraseña</a>
            <p style="color: #888; font-size: 0.8rem; margin-top: 30px;">Si tú no solicitaste esto, puedes ignorar este mensaje.</p>
        </div>
    """

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()