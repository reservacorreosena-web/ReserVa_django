from django.shortcuts import render
from comentarios.models import Resena  # <--- Importa tu modelo desde la app de comentarios
from usuarios.decorador import verificar


def home(request):
    #Esto lo utilizamos para traer todas las reseñas y pintarlas
    todas_las_resenas = Resena.objects.all().order_by('-fecha')


    contexto = {
        'reseñas': todas_las_resenas
    }


    usuario_actual = request.session.get("logueado")

    #Esta es una validacion para verificar si el usuario es administrador o cliente
    if usuario_actual and usuario_actual.get("rol") == "admin":
        return render(request, 'landing/inicio_admin.html', contexto)


    return render(request, 'landing/landing.html', contexto)