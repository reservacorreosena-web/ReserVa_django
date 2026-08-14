from django.shortcuts import render,redirect
from .models import Reserva
from django.http import HttpResponse
from usuarios.decorador import verificar
from django.contrib import messages
from .serializador import *
from rest_framework import viewsets

@verificar
def crear_reserva(request):
    if request.method == "POST":
        # Obtenemos los datos del formulario usando los 'name' de los inputs
        nombre = request.POST.get("nombre")
        telefono = request.POST.get("telefono")
        cantidad_personas = request.POST.get("cantidad_personas")
        mesa = request.POST.get("mesa")
        fecha = request.POST.get("fecha")
        hora = request.POST.get("hora")
        notas = request.POST.get("notas")
        preordenar = request.POST.get("preordenar")

        if preordenar == 'SI':
            request.session['datos_reserva_temporal'] = {
                'nombre': nombre,
                'telefono': telefono,
                'cantidad_personas': cantidad_personas,
                'mesa':mesa,
                'fecha':fecha,
                'hora': hora,
            
            }
            return redirect('ver_carta')
        else:
            nueva_reserva = Reserva(
            nombre = nombre,
            telefono = telefono,
            cantidad_personas= cantidad_personas,
            mesa=mesa,
            fecha=fecha,
            hora= hora,
            )
        
            nueva_reserva.save()
            messages.success(request, "Tu mesa ha sido reservada con éxito.")
            return redirect('mis_reservas') # O a la página que los mande normalmente

        messages.success(request, '¡Tu mesa ha sido reservada con éxito! Te esperamos.')


        return redirect('mis_reservas')

    # Si no es POST, mostramos el formulario
    return render(request, "reservas/formulario_reserva.html")

@verificar
def mis_reservas(request):
    r = Reserva.objects.all()
    contexto = {
        "reservas": r
    }

    return render(request, "reservas/mis_reservas.html", contexto)

@verificar
def cancelar_reserva(request, id):
    r = Reserva.objects.get(pk=id)
    r.delete()
    return redirect('mis_reservas')
@verificar
def actualizar_reserva(request, id):
    r = Reserva.objects.get(id=id)
    if request.method =="POST":
        r.nombre = request.POST.get('nombre')
        r.fecha = request.POST.get('fecha')
        r.hora = request.POST.get('hora')
        r.cantidad_personas = request.POST.get('cantidad_personas')
        r.telefono = request.POST.get('telefono')
        r.mesa = request.POST.get('mesa')
        r.notas = request.POST.get('notas')
        r.save()
        return redirect('mis_reservas')
    else:
        r = Reserva.objects.get(pk=id)
        contexto = {
            "datos" : r
        }
        return render(request, "reservas/editar_reserva.html", contexto)

def confirmacion(request):
    return render(request, "reservas/exito.html")


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer