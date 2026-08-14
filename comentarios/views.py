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
    if request.method == "POST":
        comida = request.POST.get("comida")
        servicio = request.POST.get("servicio")
        comentario = request.POST.get("comentario")

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