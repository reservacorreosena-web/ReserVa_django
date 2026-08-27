from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def enviar_correo_reserva(reserva):
    # Accedemos a 'email' y 'nombre' exactamente como están en tu modelo Usuario
    correo_destino = reserva.usuario.email
    nombre_cliente = reserva.usuario.nombre

    subject = '¡Tu reserva ha sido confirmada! - ReserVa'
    to = [correo_destino]
    
    text_content = f"Hola {nombre_cliente}, tu reserva en ReserVa fue confirmada para la fecha {reserva.fecha} a las {reserva.hora}."
    
    html_content = f"""
        <div style="background-color: #0a0a0a; color: #ffffff; padding: 30px; font-family: Arial, sans-serif; border-radius: 8px;">
            <h2 style="color: #c9a961; font-family: serif;">Reser<span style="color: #ffffff;">Va</span></h2>
            <p>Hola <strong>{nombre_cliente}</strong>, tu mesa en Medellín ha sido apartada con éxito.</p>
            <hr style="border: 1px solid #222;">
            <ul style="list-style: none; padding: 0; color: #888;">
                <li>📅 <strong>Fecha:</strong> {reserva.fecha}</li>
                <li>⏰ <strong>Hora:</strong> {reserva.hora}</li>
                <li>👥 <strong>Personas:</strong> {reserva.cantidad_personas}</li>
            </ul>
            <p style="color: #c9a961; margin-top: 20px;">¡Te esperamos en Medellín!</p>
        </div>
    """

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()