import os
from django.shortcuts import render, redirect, get_object_or_404
from reservas.models import Plato, Zona, Mesa
from django.contrib import messages
from django.views.decorators.http import require_POST
from usuarios.decorador import solo_admin

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from usuarios.permissions import IsUsuarioAdminOrReadOnly, get_usuario_app
from reservas.disponibilidad import (
    obtener_ocupacion,
    parse_fecha_hora,
    parse_personas,
)
from .serializador import PlatoSerializer, ZonaSerializer, MesaSerializer


def _es_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    usuario = get_usuario_app(user)
    return bool(usuario and usuario.rol == "admin")


class PlatoViewSet(viewsets.ModelViewSet):
    serializer_class = PlatoSerializer
    queryset = Plato.objects.all()
    permission_classes = [IsAuthenticated, IsUsuarioAdminOrReadOnly]

    def get_queryset(self):
        queryset = Plato.objects.all().order_by("categoria", "nombre")
        categoria = self.request.query_params.get("categoria")
        destacado = self.request.query_params.get("destacado")
        buscar = self.request.query_params.get("buscar")

        if categoria and categoria != "todos":
            queryset = queryset.filter(categoria=categoria)
        if destacado in ("1", "true", "True"):
            queryset = queryset.filter(destacado=True)
        if buscar:
            queryset = queryset.filter(nombre__icontains=buscar)

        if self.request.method in SAFE_METHODS:
            # La carta pública solo muestra platos disponibles y con stock.
            # Los administradores conservan acceso a todo el catálogo.
            if not _es_admin(self.request.user):
                queryset = queryset.filter(disponible=True, stock__gt=0)

        return queryset


class ZonaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Zona.objects.all().order_by("nombre")
    serializer_class = ZonaSerializer
    permission_classes = [IsAuthenticated]


class MesaViewSet(viewsets.ReadOnlyModelViewSet):
    """Mesas con coordenadas del plano y disponibilidad opcional.

    Sin parámetros devuelve el catálogo de mesas (igual que antes), ahora con
    ``posicion_x``/``posicion_y``. Si se envían ``fecha`` y ``hora`` (y
    opcionalmente ``personas``), añade ``disponible`` y
    ``motivo_no_disponible`` calculados con las mismas reglas del mapa web.
    """

    serializer_class = MesaSerializer
    queryset = Mesa.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Mesa.objects.all().order_by("numero")
        zona = self.request.query_params.get("zona")
        if zona:
            try:
                zona_id = int(zona)
            except (TypeError, ValueError):
                raise ValidationError({"zona": "Debe ser un número entero."})
            queryset = queryset.filter(zona_id=zona_id)
        return queryset

    def _get_disponibilidad(self, requerida=False):
        if hasattr(self, "_disponibilidad_cache"):
            return self._disponibilidad_cache

        if getattr(self, "request", None) is None:
            return None

        fecha = self.request.query_params.get("fecha")
        hora = self.request.query_params.get("hora")
        personas_raw = self.request.query_params.get("personas")

        if not any((fecha, hora, personas_raw)):
            if requerida:
                raise ValidationError(
                    {
                        "detail": (
                            "Debes indicar fecha y hora para consultar "
                            "la disponibilidad."
                        )
                    }
                )
            self._disponibilidad_cache = None
            return None

        if not fecha or not hora:
            raise ValidationError(
                {"detail": "Debes indicar fecha y hora juntas."}
            )

        fecha_obj, hora_obj = parse_fecha_hora(fecha, hora)
        personas = parse_personas(personas_raw)
        reservadas, consumos = obtener_ocupacion(fecha_obj, hora_obj)

        self._disponibilidad_cache = {
            "fecha": fecha_obj,
            "hora": hora_obj,
            "personas": personas,
            "reservadas": reservadas,
            "consumos": consumos,
        }
        return self._disponibilidad_cache

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        disponibilidad = self._get_disponibilidad(requerida=False)
        if disponibilidad:
            contexto["disponibilidad"] = disponibilidad
        return contexto

    @action(detail=False, methods=["get"], url_path="disponibles")
    def disponibles(self, request):
        """Devuelve solo las mesas libres para una fecha, hora y personas."""
        self._get_disponibilidad(requerida=True)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        mesas = [mesa for mesa in serializer.data if mesa["disponible"]]
        return Response(mesas)



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
        destacado = request.POST.get("destacado") in ('on', 'true', 'True')
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

        if imagen:
            ext = os.path.splitext(imagen.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                messages.error(request, "Solo se permiten formatos de imagen válidos (JPG, PNG, WEBP, GIF).")
                return render(request, "menu/crear_plato.html", contexto)
            if imagen.size > 5 * 1024 * 1024:
                messages.error(request, "La imagen no puede superar los 5 MB.")
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
@require_POST
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
    plato = get_object_or_404(Plato, id=id)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip().title()
        descripcion = request.POST.get("descripcion", "").capitalize()
        precio_raw = request.POST.get("precio", "")
        categoria = request.POST.get("categoria", "")
        disponible = request.POST.get("disponible") == 'on'
        destacado = request.POST.get("destacado") in ('on', 'true', 'True')
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