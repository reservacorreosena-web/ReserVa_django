from django.shortcuts import render, redirect
from .models import Resena
from django.http import HttpResponse
from django.contrib import messages
from usuarios.decorador import verificar

def crear_resena(request):
    if request.method == "POST":
        comida = request.POST.get("comida")
        servicio = request.POST.get("servicio")
        comentario = request.POST.get("comentario").strip()

        if not comida or not servicio or not comentario:
            messages.error(request,"Ingrese los campos")
            return redirect('crear_resena')

        try:
            comida1 = int(comida)
            servicio1 = int(servicio)
            if servicio1 < 0 or comida1 < 0:
                messages.error(request,"Ingrese valores validos")
                return redirect('crear_resena')
        except ValueError:
            messages.error("Debes ingresar numeros")
            return redirect('crear_resena')

        if len(comentario) <3:
            messages.error(request,"El comentario debe tener mas de 3 letras")
            return redirect('crear_resena')
        if len(comentario)>300:
            messages.warning(request,"El comentario no puede supear los 300 caracteres")
            return redirect('crear_resena')

        

        Resena.objects.create(
            usuario=request.user,
            calificacion_comida=comida,
            calificacion_servicio=servicio,
            comentario=comentario
        )

        # Enviamos un mensaje de éxito para que el base.html lo atrape
        messages.success(request, "¡Tu reseña ha sido publicada con éxito!")
        
        # Redirigimos al inicio
        return redirect('inicio')

    return render(request, "comentarios/resena.html")