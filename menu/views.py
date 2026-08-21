from django.shortcuts import render, redirect
from .models import Plato
from django.contrib import messages
from usuarios.decorador import solo_admin


@solo_admin
def listar_platos_admin(request):
    plato = Plato.objects.all()
    contexto = {
        'plato': plato
    }
    return render(request, "menu/funciones_carta.html", contexto)

def listar_platos(request):
    plato = Plato.objects.filter(disponible=True)
    contexto = {
        'plato':plato
    }
    return render(request,"menu/carta.html",contexto)


@solo_admin
def crear_plato(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip().title()
        descripcion = request.POST.get("descripcion")
        precio_raw = request.POST.get("precio")
        categoria = request.POST.get("categoria")
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") == 'on'

        if not nombre or not descripcion or not precio_raw or not categoria:
            messages.error(request,"Debes llenar todos los campos")
            return redirect('ver_carta_admin')
        try:
            precio = int(precio_raw)
            if precio <=0:
                messages.error(request, "Ingresa un valor valido.")
                return redirect('ver_carta_admin')
        except ValueError:
            messages.error(request,"Debes ingresar un numero.")
            return redirect('ver_carta_admin')

        if len(nombre)<3:
            messages.error(request, "El nombre debe tener mas de 5 caracteres")
            return redirect('ver_carta_admin')

        Plato.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria,
            disponible=disponible,
            destacado=destacado
        )
        messages.success(request, "El plato ha sido agregado correctamente.")

        # REDIRECCIÓN CORRECTA: Usamos el name de la URL, NUNCA el nombre del archivo HTML
        return redirect('ver_carta_admin')


    return render(request, "menu/crear_plato.html")
@solo_admin
def eliminar_plato(request, plato_id):
    try:
        plato = Plato.objects.get(pk=plato_id)
        plato.delete()
        messages.success(request, "El plato ha sido eliminado correctamente.")
    except Plato.DoesNotExist:
        messages.error(request, "El plato que intentas eliminar ya no existe.")
        
    return redirect('ver_carta_admin')

@solo_admin
def editar_plato(request,id):
    plato = Plato.objects.get(id=id)
    if request.method=="POST":
        nombre=request.POST.get("nombre").strip().title()
        descripcion = request.POST.get("descripcion").capitalize()
        precio_raw = request.POST.get("precio")
        categoria = request.POST.get("categoria")
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") == 'on'
        if not nombre or not descripcion or not precio_raw or not categoria:
            messages.error(request, "Todos los campos deben estar llenos")
            return redirect('editar_plato', id=id)
        try:
            precio = int(precio_raw)
            if precio <=0:
                messages.error(request,"Ingresa un valor valido.")
                return redirect('editar_plato', id=id)
        except ValueError:
            messages.error(request,"Debes ingresar un numero.")
            return redirect('editar_plato',id=id)
        if len(nombre)<3:
            messages.error(request, "El plato debe tener mas de 5 caracteres.")
            return redirect('editar_plato', id=id)
        plato.nombre = nombre
        plato.descripcion = descripcion
        plato.precio=precio
        plato.categoria=categoria
        plato.disponible=disponible
        plato.destacado=destacado
        plato.save()
        return redirect('ver_carta_admin')
    else:
        plato = Plato.objects.get(pk=id)
        contexto = {
            "platos":plato
        }
        return render(request, "menu/editar_plato.html", contexto)

