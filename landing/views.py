from django.shortcuts import render, redirect
from comentarios.models import Resena  
from usuarios.decorador import verificar
from usuarios.models import Usuario
# Importamos la vista de reservas para el admin y el modelo Plato
from reservas.views import inicio_admin 
from reservas.models import Plato  # <-- ¡Importamos el modelo Plato de reservas!

def home(request):
    usuario_actual = request.session.get("logueado")

    # Si es administrador, llamamos directamente a la función oficial de reservas que calcula todo
    if usuario_actual and usuario_actual.get("rol") == "admin":
        return inicio_admin(request)

    # Si es un cliente normal, buscamos el primer plato disponible como sugerido del día
    plato_sugerido = Plato.objects.filter(disponible=True).first()

    # Traemos las reseñas
    todas_las_resenas = Resena.objects.all().order_by('-fecha')
    
    contexto = {
        'reseñas': todas_las_resenas,
        'plato_sugerido': plato_sugerido, # <-- ¡Lo mandamos al template de la landing!
    }
    return render(request, 'landing/landing.html', contexto)


def perfil_usuario(request):
    usuario_session = request.session.get('logueado')
    if not usuario_session:
        return redirect('iniciar_sesion')
    
    usuario_db = Usuario.objects.filter(id=usuario_session.get('id')).first()

    return render(request, 'landing/perfil.html', {'usuario_datos': usuario_db})