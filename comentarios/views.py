from django.shortcuts import render, redirect
from .models import Resena
from django.http import HttpResponse
from django.contrib import messages
from usuarios.decorador import verificar


from .serializador import *
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

@verificar

def crear_resena(request):
    #Atrapamos los datos basicos del formulario
    if request.method == "POST":
        comida = request.POST.get("comida")
        servicio = request.POST.get("servicio")
        comentario = request.POST.get("comentario").strip()

        #Con esto validamos que todos los datos esten llenos
        if not comida or not servicio or not comentario:
            messages.error(request,"Ingrese los campos")
            return redirect('crear_resena')
        #creamos variables nuevas asegurando que los datos que tengan sean INT y empezamos con sus validaciones
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

        
        #Aca ya creamos el objeto
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

class ResenaViewSet(viewsets.ModelViewSet):
    queryset = Resena.objects.all()
    serializer_class = ResenaSerializer