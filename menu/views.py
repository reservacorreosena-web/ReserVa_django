from django.shortcuts import render, redirect
from reservas.models import Plato
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
  categoria_seleccionada = request.GET.get('categoria', 'todos')

  if categoria_seleccionada != 'todos':
    platos = Plato.objects.filter(
        disponible=True, categoria=categoria_seleccionada, stock__gt=0
    )
  else:
    platos = Plato.objects.filter(disponible=True, stock__gt=0)

  contexto = {'plato': platos, 'categoria_actual': categoria_seleccionada}
  return render(request, 'menu/carta.html', contexto)

@solo_admin
def crear_plato(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip().title()
        descripcion = request.POST.get("descripcion", "")
        precio_raw = request.POST.get("precio", "")
        categoria = request.POST.get("categoria", "")
        imagen = request.FILES.get('imagen')
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") == 'on'
        stock_raw = request.POST.get("stock", "")

        datos_plato = {
            "nombre": nombre,
            "descripcion": descripcion,
            "precio_raw": precio_raw,
            "categoria": categoria,
            "stock": stock_raw
        }

        contexto = {
            "datos_plato": datos_plato
        }

        if not nombre or not descripcion or not precio_raw or not categoria or not stock_raw:
            messages.error(request, "Debes llenar todos los campos")
            return render(request, "menu/crear_plato.html", contexto)

        try:
            precio = int(precio_raw)
            if precio <= 0:
                messages.error(request, "Ingresa un valor valido para el precio.")
                return render(request, "menu/crear_plato.html", contexto)
        except ValueError:
            messages.error(request, "El precio debe ser un número.")
            return render(request, "menu/crear_plato.html", contexto)

        try:
            stock = int(stock_raw)
            if stock < 0:
                messages.error(request, "El stock no puede ser negativo.")
                return render(request, "menu/crear_plato.html", contexto)
        except ValueError:
            messages.error(request, "El stock debe ser un número válido.")
            return render(request, "menu/crear_plato.html", contexto)

        if len(nombre) < 3:
            messages.error(request, "El nombre debe tener al menos 3 caracteres.")
            return render(request, "menu/crear_plato.html", contexto)

        # Creación en la base de datos (Incluyendo stock e imagen)
        Plato.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria,
            disponible=disponible,
            destacado=destacado,
            stock=stock,
            imagen=imagen
        )
        messages.success(request, "El plato ha sido agregado correctamente.")
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
def editar_plato(request, id):
    plato = Plato.objects.get(id=id)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip().title()
        descripcion = request.POST.get("descripcion", "").capitalize()
        precio_raw = request.POST.get("precio", "")
        categoria = request.POST.get("categoria", "")
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") == 'on'
        stock_raw = request.POST.get("stock", "")

        if not nombre or not descripcion or not precio_raw or not categoria or not stock_raw:
            messages.error(request, "Todos los campos deben estar llenos")
            return redirect('editar_plato', id=id)

        try:
            precio = int(precio_raw)
            if precio <= 0:
                messages.error(request, "Ingresa un valor válido para el precio.")
                return redirect('editar_plato', id=id)
        except ValueError:
            messages.error(request, "El precio debe ser un número.")
            return redirect('editar_plato', id=id)

        try:
            stock = int(stock_raw)
            if stock < 0:
                messages.error(request, "El stock no puede ser negativo.")
                return redirect('editar_plato', id=id)
        except ValueError:
            messages.error(request, "El stock debe ser un número válido.")
            return redirect('editar_plato', id=id)

        if len(nombre) < 3:
            messages.error(request, "El plato debe tener más de 3 caracteres.")
            return redirect('editar_plato', id=id)

        plato.nombre = nombre
        plato.descripcion = descripcion
        plato.precio = precio
        plato.categoria = categoria
        plato.disponible = disponible
        plato.destacado = destacado
        plato.stock = stock
        plato.save()

        messages.success(request, "Plato actualizado correctamente.")
        return redirect('ver_carta_admin')
    else:
        contexto = {
            "platos": plato
        }
        return render(request, "menu/editar_plato.html", contexto)