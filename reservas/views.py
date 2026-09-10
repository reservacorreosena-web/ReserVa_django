from datetime import datetime
import json
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from usuarios.decorador import solo_admin, verificar
from usuarios.models import Usuario
from .models import ConsumoMesa, Mesa, Plato, Reserva, Zona
from .utils import enviar_correo_reserva


@verificar
def crear_reserva(request):
  # Recuperamos los platos con stock para la preselección
  platos_disponibles = Plato.objects.filter(disponible=True, stock__gt=0)

  if request.method == "POST":
    usuario_session = request.session.get("logueado")
    if not usuario_session:
      messages.error(request, "Debes iniciar sesión para realizar una reserva.")
      return redirect("login")

    usuario_id = (
        usuario_session.get("id")
        if isinstance(usuario_session, dict)
        else usuario_session
    )

    cantidad_personas = request.POST.get("cantidad_personas", "").strip()
    fecha = request.POST.get("fecha", "").strip()
    hora = request.POST.get("hora", "").strip()
    notas = request.POST.get("notas", "").strip()
    preordenar = request.POST.get("preordenar", "NO")

    # Capturamos los IDs de los platos seleccionados mediante checkboxes
    platos_seleccionados = request.POST.getlist("platos[]")

    datos_formulario = {
        "cantidad_personas": cantidad_personas,
        "fecha": fecha,
        "hora": hora,
        "notas": notas,
    }

    contexto_error = {"datos": datos_formulario, "platos": platos_disponibles}

    if not cantidad_personas or not fecha or not hora:
      messages.error(
          request, "Por favor completa la cantidad de personas, fecha y hora."
      )
      return render(request, "reservas/formulario_reserva.html", contexto_error)

    try:
      personas = int(cantidad_personas)
      if personas <= 0 or personas > 20:
        messages.error(
            request, "La cantidad de personas debe ser entre 1 y 20."
        )
        return render(
            request, "reservas/formulario_reserva.html", contexto_error
        )
    except ValueError:
      messages.error(request, "Ingresa un número válido para las personas.")
      return render(request, "reservas/formulario_reserva.html", contexto_error)

    # Guardamos los datos temporales incluyendo los platos elegidos
    request.session["datos_reserva_temporal"] = {
        "usuario_id": usuario_id,
        "cantidad_personas": personas,
        "fecha": fecha,
        "hora": hora,
        "notas": notas,
        "platos_ids": [int(p_id) for p_id in platos_seleccionados],
    }

    return redirect("seleccionar_mesa_mapa")

  contexto = {"platos": platos_disponibles}
  return render(request, "reservas/formulario_reserva.html", contexto)


@verificar
def seleccionar_mesa_mapa(request):
  datos_temp = request.session.get("datos_reserva_temporal")
  if not datos_temp:
    messages.error(request, "Primero debes completar los datos de tu reserva.")
    return redirect("crear_reserva")

  fecha = datos_temp["fecha"]
  hora = datos_temp["hora"]
  personas_requeridas = datos_temp["cantidad_personas"]

  mesas_por_reserva_ids = Reserva.objects.filter(
      fecha=fecha, hora=hora, estado__in=["pendiente", "confirmada", "asistio"]
  ).values_list("mesa_id", flat=True)

  mesas_con_consumo_ids = ConsumoMesa.objects.filter(pagado=False).values_list(
      "mesa_id", flat=True
  )
  mesas_ocupadas_ids = set(
      list(mesas_por_reserva_ids) + list(mesas_con_consumo_ids)
  )

  todas_las_mesas = Mesa.objects.all()

  if request.method == "POST":
    mesa_id = request.POST.get("mesa_id")

    if int(mesa_id) in mesas_ocupadas_ids:
      messages.error(
          request,
          "Lo sentimos, esta mesa acaba de ser ocupada o tiene un consumo"
          " activo.",
      )
      return redirect("seleccionar_mesa_mapa")

    mesa_seleccionada = get_object_or_404(Mesa, id=mesa_id)

    usuario_session = request.session.get("logueado")
    usuario_id = (
        usuario_session.get("id")
        if isinstance(usuario_session, dict)
        else usuario_session
    )
    usuario_instancia = get_object_or_404(Usuario, id=usuario_id)

    # 1. Creamos la reserva principal
    nueva_reserva = Reserva.objects.create(
        usuario=usuario_instancia,
        mesa=mesa_seleccionada,
        cantidad_personas=personas_requeridas,
        fecha=fecha,
        hora=hora,
        notas=datos_temp.get("notas", ""),
        estado="pendiente",
    )

    # ==========================================================
    # 2. AQUÍ AGREGAS LA LÓGICA PARA RESTAR EL STOCK Y REGISTRAR EL CONSUMO
    # ==========================================================
    platos_ids = datos_temp.get("platos_ids", [])
    for plato_id in platos_ids:
      try:
        plato_obj = Plato.objects.get(id=plato_id)
        if plato_obj.stock > 0:
          plato_obj.stock -= 1  # Resta una unidad del stock global
          plato_obj.save()

          # Lo registramos de una vez en el consumo de la mesa
          ConsumoMesa.objects.create(
              mesa=mesa_seleccionada,
              reserva=nueva_reserva,
              plato=plato_obj,
              cantidad=1,
              precio_unitario=plato_obj.precio,
          )
      except Plato.DoesNotExist:
        continue
    # ==========================================================

    try:
      enviar_correo_reserva(nueva_reserva)
    except Exception as e:
      print(f"Error al enviar el correo de confirmación: {e}")

    del request.session["datos_reserva_temporal"]
    messages.success(
        request, f"¡Mesa #{mesa_seleccionada.numero} reservada con éxito!"
    )
    return redirect("mis_reservas")

  contexto = {
      "mesas": todas_las_mesas,
      "mesas_ocupadas_ids": list(mesas_ocupadas_ids),
      "datos": datos_temp,
  }
  return render(request, "reservas/mapa_mesas.html", contexto)


@verificar
def mis_reservas(request):
  usuario_session = request.session.get("logueado")
  usuario_id = usuario_session.get("id")

  reservas = (
      Reserva.objects.filter(usuario_id=usuario_id)
      .exclude(estado="cancelada")
      .order_by("-id")
  )

  contexto = {"reservas": reservas}
  return render(request, "reservas/mis_reservas.html", contexto)


@verificar
def cancelar_reserva(request, id):
  usuario_session = request.session.get("logueado")
  usuario_id = usuario_session.get("id")

  reserva = get_object_or_404(Reserva, id=id, usuario_id=usuario_id)
  reserva.estado = "cancelada"
  reserva.save()

  messages.info(request, "La reserva ha sido cancelada exitosamente.")
  return redirect("mis_reservas")


@verificar
def actualizar_reserva(request, id):
  usuario_session = request.session.get("logueado")
  usuario_id = usuario_session.get("id")

  reserva = get_object_or_404(Reserva, id=id, usuario_id=usuario_id)

  if request.method == "POST":
    cantidad_personas = request.POST.get("cantidad_personas", "").strip()
    fecha = request.POST.get("fecha", "").strip()
    hora = request.POST.get("hora", "").strip()
    notas = request.POST.get("notas", "").strip()

    if not cantidad_personas or not fecha or not hora:
      messages.error(
          request, "Todos los campos obligatorios deben estar diligenciados."
      )
      return redirect("actualizar_reserva", id=id)

    try:
      personas = int(cantidad_personas)
      if personas <= 0 or personas > 20:
        messages.error(
            request, "La cantidad de personas debe ser entre 1 y 20."
        )
        return redirect("actualizar_reserva", id=id)
    except ValueError:
      messages.error(request, "La cantidad de personas no es válida.")
      return redirect("actualizar_reserva", id=id)

    reserva.cantidad_personas = personas
    reserva.fecha = fecha
    reserva.hora = hora
    reserva.notas = notas
    reserva.save()

    messages.success(request, "Reserva actualizada correctamente.")
    return redirect("mis_reservas")

  contexto = {"datos": reserva}
  return render(request, "reservas/editar_reserva.html", contexto)


def confirmacion(request):
  return render(request, "reservas/exito.html")


@solo_admin
def historial_reservas(request):
  reservas = Reserva.objects.all().order_by("-fecha", "-hora")

  busqueda = request.GET.get("buscar")
  filtro_estado = request.GET.get("filtro_estado")
  filtro_fecha = request.GET.get("filtro_fecha")

  if busqueda:
    reservas = reservas.filter(
        Q(id__icontains=busqueda) | Q(usuario__nombre__icontains=busqueda)
    )

  if filtro_estado:
    reservas = reservas.filter(estado__iexact=filtro_estado)

  if filtro_fecha:
    reservas = reservas.filter(fecha=filtro_fecha)

  # Métricas para las tarjetas superiores adaptadas a tus estados
  total_reservas = Reserva.objects.count()
  asistio = Reserva.objects.filter(estado__iexact="asistio").count()
  pendientes = Reserva.objects.filter(estado__iexact="pendiente").count()
  canceladas = Reserva.objects.filter(estado__iexact="cancelada").count()

  contexto = {
      "reservas": reservas,
      "total_reservas": total_reservas,
      "asistio": asistio,
      "pendientes": pendientes,
      "canceladas": canceladas,
  }
  return render(request, "reservas/historial_reservas.html", contexto)


@solo_admin  # <--- Blindado: Solo administradores pueden cambiar estados por URL
def cambiar_estado_reserva(request, id, nuevo_estado):
  reservas = get_object_or_404(Reserva, id=id)
  estados_valido = ["asistio", "pendiente", "cancelada", "confirmada"]
  if nuevo_estado in estados_valido:
    reservas.estado = nuevo_estado
    reservas.save()
    messages.success(request, f"La reserva #{reservas.id} ha sido actualizada")
  else:
    messages.error(request, "Estado no válido.")

  return redirect("historial_reservas")


@solo_admin  # <--- Blindado: Clientes curiosos no pueden entrar al mapa de administración
def admin_mapa_mesas(request):
  fecha = request.GET.get(
      "fecha", timezone.now().date().strftime("%Y-%m-%d")
  )
  hora = request.GET.get("hora", timezone.now().strftime("%H:%M"))

  todas_las_mesas = Mesa.objects.all().order_by("zona", "numero")

  reservas_en_horario = Reserva.objects.filter(
      fecha=fecha, hora=hora, estado__in=["pendiente", "confirmada", "asistio"]
  ).select_related("usuario", "mesa")
  mapa_reservas = {r.mesa_id: r for r in reservas_en_horario}

  consumos_activos = ConsumoMesa.objects.filter(pagado=False)

  totales_consumo = {}
  mesas_con_consumo = set()

  for consumo in consumos_activos:
    mesas_con_consumo.add(consumo.mesa_id)
    totales_consumo[consumo.mesa_id] = (
        totales_consumo.get(consumo.mesa_id, 0) + consumo.subtotal()
    )

  contexto = {
      "mesas": todas_las_mesas,
      "mapa_reservas": mapa_reservas,
      "mesas_con_consumo": mesas_con_consumo,
      "totales_consumo": totales_consumo,
      "fecha": fecha,
      "hora": hora,
  }
  return render(request, "reservas/admin_mapa.html", contexto)


@solo_admin  # <--- Blindado: Solo admins pueden ver los detalles de consumos de las mesas
def admin_detalle_mesa(request, mesa_id):
  mesa = get_object_or_404(Mesa, id=mesa_id)

  consumos = ConsumoMesa.objects.filter(mesa=mesa, pagado=False).select_related(
      "plato"
  )
  total_cuenta = sum(c.subtotal() for c in consumos)

  query = request.GET.get("q", "").strip()
  platos = Plato.objects.filter(disponible=True)
  if query:
    platos = platos.filter(nombre__icontains=query)

  contexto = {
      "mesa": mesa,
      "consumos": consumos,
      "total_cuenta": total_cuenta,
      "platos": platos,
      "query": query,
  }
  return render(request, "reservas/admin_detalle_mesa.html", contexto)


@solo_admin  # <--- Blindado: Solo administradores agregan items al POS
def admin_agregar_al_carrito(request, mesa_id, plato_id):
  if request.method == "POST":
    mesa = get_object_or_404(Mesa, id=mesa_id)
    plato = get_object_or_404(Plato, id=plato_id)

    try:
      cantidad = int(request.POST.get("cantidad", 1))
      if cantidad <= 0 or cantidad > 100:
        messages.error(request, "La cantidad debe ser entre 1 y 100.")
        return redirect("admin_detalle_mesa", mesa_id=mesa_id)
    except ValueError:
      messages.error(request, "Ingresa un número de cantidad válido.")
      return redirect("admin_detalle_mesa", mesa_id=mesa_id)

    # Validación de Stock disponible
    if plato.stock < cantidad:
      messages.error(
          request,
          f"Stock insuficiente. Solo quedan {plato.stock} unidades de"
          f" {plato.nombre}.",
      )
      return redirect("admin_detalle_mesa", mesa_id=mesa_id)

    consumo_existente = ConsumoMesa.objects.filter(
        mesa=mesa, plato=plato, pagado=False
    ).first()

    if consumo_existente:
      consumo_existente.cantidad += cantidad
      consumo_existente.save()
    else:
      reserva_activa = Reserva.objects.filter(
          mesa=mesa,
          fecha=timezone.now().date(),
          estado__in=["pendiente", "confirmada", "asistio"],
      ).first()

      ConsumoMesa.objects.create(
          mesa=mesa,
          reserva=reserva_activa,
          plato=plato,
          cantidad=cantidad,
          precio_unitario=plato.precio,
      )

    # Descontar del stock global del plato
    plato.stock -= cantidad
    plato.save()

  return redirect("admin_detalle_mesa", mesa_id=mesa_id)


@solo_admin
def admin_eliminar_item_carrito(request, consumo_id):
  consumo = get_object_or_404(ConsumoMesa, id=consumo_id)
  mesa_id = consumo.mesa.id


  plato = consumo.plato
  plato.stock += consumo.cantidad
  plato.save()

  consumo.delete()
  return redirect("admin_detalle_mesa", mesa_id=mesa_id)


@solo_admin  # <--- Blindado: Solo administradores pueden cerrar cuentas
def admin_cobrar_mesa(request, mesa_id):
  ConsumoMesa.objects.filter(mesa_id=mesa_id, pagado=False).update(pagado=True)
  Reserva.objects.filter(
      mesa_id=mesa_id,
      fecha=timezone.now().date(),
      estado__in=["pendiente", "confirmada", "asistio"],
  ).update(estado="completada")
  return redirect("admin_mapa_mesas")


@solo_admin
def inicio_admin(request):
  hoy = timezone.now().date()
  reservas_hoy_qs = Reserva.objects.filter(fecha=hoy)

  comandas_hoy = ConsumoMesa.objects.filter(mesa__reserva__fecha=hoy)
  ventas_totales_hoy = sum(c.subtotal() for c in comandas_hoy)

  estados_conteo = reservas_hoy_qs.values("estado").annotate(
      total=Count("id")
  )
  estados_nombres = [item["estado"].capitalize() for item in estados_conteo]
  estados_valores = [item["total"] for item in estados_conteo]

  if not estados_nombres:
    estados_nombres = ["Sin reservas hoy"]
    estados_valores = [0]

  top_platos = (
      ConsumoMesa.objects.values("plato__nombre")
      .annotate(total_cantidad=Sum("cantidad"))
      .order_by("-total_cantidad")[:5]
  )
  platos_labels = [
      p["plato__nombre"] if p["plato__nombre"] else "Sin nombre"
      for p in top_platos
  ]
  platos_data = [p["total_cantidad"] for p in top_platos]

  if not platos_labels:
    platos_labels = ["Sin datos aún"]
    platos_data = [0]

  reservas_por_zona = (
      reservas_hoy_qs.values("mesa__zona__nombre")
      .annotate(total=Count("id"))
      .order_by("-total")
  )
  zonas_labels = [
      z["mesa__zona__nombre"] if z["mesa__zona__nombre"] else "General"
      for z in reservas_por_zona
  ]
  zonas_data = [z["total"] for z in reservas_por_zona]

  if not zonas_labels:
    zonas_labels = ["Sin asignar"]
    zonas_data = [0]

  contexto = {
      "reservas_hoy": reservas_hoy_qs.count(),
      "pendientes_hoy": reservas_hoy_qs.filter(
          estado__iexact="pendiente"
      ).count(),
      "confirmadas_hoy": reservas_hoy_qs.filter(
          estado__iexact="confirmada"
      ).count(),
      "ventas_totales_hoy": ventas_totales_hoy,
      "total_platos": Plato.objects.count(),
      "total_usuarios": Usuario.objects.count(),
      "estados_nombres": json.dumps(estados_nombres),
      "estados_valores": json.dumps(estados_valores),
      "platos_labels": json.dumps(platos_labels),
      "platos_data": json.dumps(platos_data),
      "zonas_labels": json.dumps(zonas_labels),
      "zonas_data": json.dumps(zonas_data),
  }

  return render(request, "landing/inicio_admin.html", contexto)


@solo_admin  # <--- Blindado
def admin_enviar_pedido(request, mesa_id):
  mesa = get_object_or_404(Mesa, id=mesa_id)
  messages.success(request, f"Pedido de la mesa #{mesa.numero} enviado correctamente.")
  return redirect('admin_detalle_mesa', mesa_id=mesa_id)