from django.shortcuts import render,redirect
from .models import Reserva
from django.http import HttpResponse
from usuarios.decorador import verificar
from django.contrib import messages
@verificar
def crear_reserva(request):
    if request.method == "POST":
        # Obtenemos los datos del formulario usando los 'name' de los inputs
        nombre = request.POST.get("nombre").strip().title()
        telefono = request.POST.get("telefono").strip()
        cantidad_personas = request.POST.get("cantidad_personas")
        mesa = request.POST.get("mesa")
        fecha = request.POST.get("fecha")
        hora = request.POST.get("hora")
        notas = request.POST.get("notas")
        preordenar = request.POST.get("preordenar")

        if not nombre or not telefono or not cantidad_personas or not mesa or not fecha or not hora:
            messages.error(request, "Por favor llene todos los campos")
            return redirect('crear_reserva')

        if not telefono.isdigit() or len(telefono)<9:
            messages.error(request,"El telefono debe ser un numero valido.")
            return redirect('crear_reserva')
        if len(nombre)<3 or not nombre.replace(" ","").isalpha():  
            messages.error(request,"El nombre debe tener al menos 3 caracteres y no puede tener numeros")
            return redirect('crear_reserva')
        if len(cantidad_personas)>20:
            messages.warning(request,"Las reservas no pueden superar las 20 personas")
            return redirect('crear_reserva')
        try:
            personas = int(cantidad_personas)
            if personas <= 0:
                messages.error(request,"La cantidad de personas debe ser mayor a 0.")
        except ValueError:
            messages.error(request, "Ingrese un caracter valido.")

        
            pass
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
        r.nombre = request.POST.get('nombre').strip()
        r.fecha = request.POST.get('fecha')
        r.hora = request.POST.get('hora')
        r.cantidad_personas = request.POST.get('cantidad_personas')
        r.telefono = request.POST.get('telefono').strip()
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


