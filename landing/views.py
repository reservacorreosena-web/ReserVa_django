from django.shortcuts import render, redirect
from comentarios.models import Resena  
from usuarios.decorador import verificar
from usuarios.models import Usuario
# Importa la vista de reservas para usarla cuando sea admin
from reservas.views import inicio_admin 

def home(request):
    usuario_actual = request.session.get("logueado")

    # Si es administrador, llamamos directamente a la función oficial de reservas que calcula todo
    if usuario_actual and usuario_actual.get("rol") == "admin":
        return inicio_admin(request)

    # Si es un cliente normal, carga la landing page con sus reseñas
    todas_las_resenas = Resena.objects.all().order_by('-fecha')
    contexto = {
        'reseñas': todas_las_resenas
    }
    return render(request, 'landing/landing.html', contexto)


def perfil_usuario(request):
    usuario_session = request.session.get('logueado')
    if not usuario_session:
        return redirect('iniciar_sesion')
    
    usuario_db = Usuario.objects.filter(id=usuario_session.get('id')).first()

    return render(request, 'landing/perfil.html', {'usuario_datos': usuario_db})