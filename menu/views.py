from django.shortcuts import render, redirect
from .models import Plato
from django.contrib import messages


# 1. Lista los platos en la tabla (funciones_carta.html)
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


# 2. Muestra el formulario (GET) y procesa la creación (POST)
def crear_plato(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip().title()
        descripcion = request.POST.get("descripcion").Capitalize()
        precio = request.POST.get("precio")
        categoria = request.POST.get("categoria")
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") == 'on'

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

def eliminar_plato(request,plato_id):
    plato = Plato.objects.get(pk=plato_id)
    plato.delete()
    messages.alert=("Seguro que quieres eliminar este plato?")
    return redirect('ver_carta_admin')


def editar_plato(request,id):
    plato = Plato.objects.get(id=id)
    if request.method=="POST":
        plato.nombre=request.POST.get("nombre").strip().title()
        plato.descripcion = request.POST.get("descripcion").capitalize()
        plato.precio = request.POST.get("precio")
        plato.categoria = request.POST.get("categoria")
        plato.disponible = request.POST.get("disponible") == 'on'
        plato.destacado = request.POST.get("destacado") == 'on'
        plato.save()
        return redirect('ver_carta_admin')
    else:
        plato = Plato.objects.get(pk=id)
        contexto = {
            "platos":plato
        }
        return render(request, "menu/editar_plato.html", contexto)

