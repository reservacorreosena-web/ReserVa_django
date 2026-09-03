from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reserva, Mesa, Zona, Plato, ConsumoMesa
from usuarios.models import Usuario
from usuarios.decorador import verificar, solo_admin
from django.db.models import Q, Count, Sum
from .utils import enviar_correo_reserva
import json


@verificar
def crear_reserva(request):
    if request.method == "POST":
        # 1. Verifica las credenciales del usuario logueado con seguridad
        usuario_session = request.session.get('logueado')
        if not usuario_session:
            messages.error(request, "Debes iniciar sesión para realizar una reserva.")
            return redirect('login')

        usuario_id = usuario_session.get('id') if isinstance(usuario_session, dict) else usuario_session
        usuario_instancia = get_object_or_404(Usuario, id=usuario_id)

        # 2. Captura de datos del formulario
        cantidad_personas = request.POST.get("cantidad_personas", "").strip()
        fecha = request.POST.get("fecha", "").strip()
        hora = request.POST.get("hora", "").strip()
        notas = request.POST.get("notas", "").strip()
        preordenar = request.POST.get("preordenar", "NO")
        
        datos_formulario = {
            "cantidad_personas": cantidad_personas,
            "fecha": fecha,
            "hora": hora,
            "notas": notas
        }

        # --- VALIDACIONES DE NEGOCIO ---
        if not cantidad_personas or not fecha or not hora:
            messages.error(request, "Por favor completa la cantidad de personas, fecha y hora.")
            return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})

        try:
            personas = int(cantidad_personas)
            if personas <= 0:
                messages.error(request, "La cantidad de personas debe ser mayor a 0.")
                return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})
            if personas > 20:
                messages.warning(request, "Las reservas no pueden superar las 20 personas.")
                return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})
        except ValueError:
            messages.error(request, "Ingresa un número válido para las personas.")
            return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})

        try:
            fecha_reserva_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            if fecha_reserva_dt < datetime.now():
                messages.error(request, "No puedes realizar una reserva para una fecha u hora pasadas.")
                return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})
        except ValueError:
            messages.error(request, "El formato de fecha u hora es inválido.")
            return render(request, 'reservas/formulario_reserva.html', {"datos": datos_formulario})

        # Redirección a carta si decide preordenar
        if preordenar == 'SI':
            request.session['datos_reserva_temporal'] = {
                'usuario_id': usuario_id,
                'cantidad_personas': personas,
                'fecha': fecha,
                'hora': hora,
                'notas': notas
            }
            return redirect('ver_carta')

        # Guardamos los datos temporales y lo mandamos a el mapa de seleccionar mesas
        request.session['datos_reserva_temporal'] = {
            'usuario_id': usuario_id,
            'cantidad_personas': personas,
            'fecha': fecha,
            'hora': hora,
            'notas': notas
        }
        return redirect('seleccionar_mesa_mapa')

    return render(request, "reservas/formulario_reserva.html")


@verificar
def seleccionar_mesa_mapa(request):
    datos_temp = request.session.get('datos_reserva_temporal')
    if not datos_temp:
        messages.error(request, "Primero debes completar los datos de tu reserva.")
        return redirect('crear_reserva')

    fecha = datos_temp['fecha']
    hora = datos_temp['hora']
    personas_requeridas = datos_temp['cantidad_personas']

    mesas_ocupadas_ids = Reserva.objects.filter(
        fecha=fecha,
        hora=hora,
        estado='pendiente'
    ).values_list('mesa_id', flat=True)

    todas_las_mesas = Mesa.objects.all()

    if request.method == "POST":
        mesa_id = request.POST.get("mesa_id")
        mesa_seleccionada = get_object_or_404(Mesa, id=mesa_id)

        usuario_session = request.session.get('logueado')
        usuario_id = usuario_session.get('id') if isinstance(usuario_session, dict) else usuario_session
        usuario_instancia = get_object_or_404(Usuario, id=usuario_id)

        nueva_reserva = Reserva.objects.create(
            usuario=usuario_instancia,
            mesa=mesa_seleccionada,
            cantidad_personas=personas_requeridas,
            fecha=fecha,
            hora=hora,
            notas=datos_temp.get('notas', ''),
            estado='pendiente'
        )

        try:
            enviar_correo_reserva(nueva_reserva)
        except Exception as e:
            print(f"Error al enviar el correo de confirmación: {e}")

        del request.session['datos_reserva_temporal']
        messages.success(request, f"¡Mesa #{mesa_seleccionada.numero} reservada con éxito!")
        return redirect('mis_reservas')

    contexto = {
        "mesas": todas_las_mesas,
        "mesas_ocupadas_ids": list(mesas_ocupadas_ids),
        "datos": datos_temp
    }
    return render(request, "reservas/mapa_mesas.html", contexto)


@verificar
def mis_reservas(request):
    usuario_session = request.session.get('logueado')
    usuario_id = usuario_session.get('id')

    # Filtra por el usuario y excluye las que tengan estado 'cancelada'
    reservas = Reserva.objects.filter(usuario_id=usuario_id).exclude(estado='cancelada').order_by('-id')

    contexto = {
        "reservas": reservas
    }
    return render(request, "reservas/mis_reservas.html", contexto)


@verificar
def cancelar_reserva(request, id):
    usuario_session = request.session.get('logueado')
    usuario_id = usuario_session.get('id')

    reserva = get_object_or_404(Reserva, id=id, usuario_id=usuario_id)
    reserva.estado = 'cancelada'
    reserva.save()

    messages.info(request, "La reserva ha sido cancelada exitosamente.")
    return redirect('mis_reservas')


@verificar
def actualizar_reserva(request, id):
    usuario_session = request.session.get('logueado')
    usuario_id = usuario_session.get('id')

    reserva = get_object_or_404(Reserva, id=id, usuario_id=usuario_id)

    if request.method == "POST":
        cantidad_personas = request.POST.get('cantidad_personas', '').strip()
        fecha = request.POST.get('fecha', '').strip()
        hora = request.POST.get('hora', '').strip()
        notas = request.POST.get('notas', '').strip()

        if not cantidad_personas or not fecha or not hora:
            messages.error(request, "Todos los campos obligatorios deben estar diligenciados.")
            return redirect('actualizar_reserva', id=id)

        try:
            personas = int(cantidad_personas)
            if personas <= 0 or personas > 20:
                messages.error(request, "La cantidad de personas debe ser entre 1 y 20.")
                return redirect('actualizar_reserva', id=id)
        except ValueError:
            messages.error(request, "La cantidad de personas no es válida.")
            return redirect('actualizar_reserva', id=id)

        # Actualizar datos de la reserva
        reserva.cantidad_personas = personas
        reserva.fecha = fecha
        reserva.hora = hora
        reserva.notas = notas
        reserva.save()

        messages.success(request, "Reserva actualizada correctamente.")
        return redirect('mis_reservas')

    contexto = {
        "datos": reserva
    }
    return render(request, "reservas/editar_reserva.html", contexto)


def confirmacion(request):
    return render(request, "reservas/exito.html")


@solo_admin
def historial_reservas(request):
  # El admin puede consultar el histórico global de todos los usuarios
  reservas = Reserva.objects.all().order_by('-fecha', '-hora')

  # Capturamos los campos del formulario GET del HTML
  busqueda = request.GET.get('buscar')
  filtro_estado = request.GET.get('filtro_estado')  
  filtro_fecha = request.GET.get('filtro_fecha')

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
  asistio = Reserva.objects.filter(estado__iexact='asistio').count()
  pendientes = Reserva.objects.filter(estado__iexact='pendiente').count()
  canceladas = Reserva.objects.filter(estado__iexact='cancelada').count()

  contexto = {
      'reservas': reservas,
      'total_reservas': total_reservas,
      'asistio': asistio,
      'pendientes': pendientes,
      'canceladas': canceladas,
  }
  return render(request, 'reservas/historial_reservas.html', contexto)


def cambiar_estado_reserva(request, id, nuevo_estado):
    reservas = get_object_or_404(Reserva, id=id)
    estados_valido = ['asistio', 'pendiente', 'cancelada', 'confirmada']
    if nuevo_estado in estados_valido:
        reservas.estado = nuevo_estado
        reservas.save()
        messages.success(request, f"La reserva #{reservas.id} ha sido actualizada")
    else:
        messages.error(request, "Estado no válido.")

    return redirect('historial_reservas')


def admin_mapa_mesas(request):
    fecha = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    hora = request.GET.get('hora', timezone.now().strftime('%H:%M'))

    todas_las_mesas = Mesa.objects.all().order_by('zona', 'numero')

    reservas_en_horario = Reserva.objects.filter(
        fecha=fecha,
        hora=hora,
        estado__in=['pendiente', 'confirmada', 'asistio']
    ).select_related('usuario', 'mesa')
    mapa_reservas = {r.mesa_id: r for r in reservas_en_horario}

    # Verificamos cuáles mesas tienen consumos activos (para marcarlas visualmente)
    mesas_con_consumo = set(ConsumoMesa.objects.filter(pagado=False).values_list('mesa_id', flat=True))

    contexto = {
        'mesas': todas_las_mesas,
        'mapa_reservas': mapa_reservas,
        'mesas_con_consumo': mesas_con_consumo,
        'fecha': fecha,
        'hora': hora,
    }
    return render(request, 'reservas/admin_mapa.html', contexto)


def admin_detalle_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)

    # Consumos actuales de la mesa (el "carrito" activo)
    consumos = ConsumoMesa.objects.filter(mesa=mesa, pagado=False).select_related('plato')
    total_cuenta = sum(c.subtotal() for c in consumos)

    # Buscador de platos en la carta
    query = request.GET.get('q', '')
    platos = Plato.objects.filter(disponible=True)
    if query:
        platos = platos.filter(nombre__icontains=query)

    contexto = {
        'mesa': mesa,
        'consumos': consumos,
        'total_cuenta': total_cuenta,
        'platos': platos,
        'query': query,
    }
    return render(request, 'reservas/admin_detalle_mesa.html', contexto)


def admin_agregar_al_carrito(request, mesa_id, plato_id):
    if request.method == 'POST':
        mesa = get_object_or_404(Mesa, id=mesa_id)
        plato = get_object_or_404(Plato, id=plato_id)
        cantidad = int(request.POST.get('cantidad', 1))

        # Buscamos si ya existe este plato en la comanda actual de la mesa para sumarlo
        consumo_existente = ConsumoMesa.objects.filter(mesa=mesa, plato=plato, pagado=False).first()

        if consumo_existente:
            consumo_existente.cantidad += cantidad
            consumo_existente.save()
        else:
            reserva_activa = Reserva.objects.filter(
                mesa=mesa,
                fecha=timezone.now().date(),
                estado__in=['pendiente', 'confirmada', 'asistio']
            ).first()

            ConsumoMesa.objects.create(
                mesa=mesa,
                reserva=reserva_activa,
                plato=plato,
                cantidad=cantidad,
                precio_unitario=plato.precio
            )

    return redirect('admin_detalle_mesa', mesa_id=mesa_id)


def admin_eliminar_item_carrito(request, consumo_id):
    consumo = get_object_or_404(ConsumoMesa, id=consumo_id)
    mesa_id = consumo.mesa.id
    consumo.delete()
    return redirect('admin_detalle_mesa', mesa_id=mesa_id)


def admin_cobrar_mesa(request, mesa_id):
    ConsumoMesa.objects.filter(mesa_id=mesa_id, pagado=False).update(pagado=True)
    Reserva.objects.filter(
        mesa_id=mesa_id,
        fecha=timezone.now().date(),
        estado__in=['pendiente', 'confirmada', 'asistio']
    ).update(estado='completada')
    return redirect('admin_mapa_mesas')


@solo_admin
def inicio_admin(request):
    # Obtener la fecha de hoy del sistema
    hoy = timezone.now().date()
    
    # Filtrar las reservas de hoy para calcular las métricas del dashboard
    reservas_hoy_qs = Reserva.objects.filter(fecha=hoy)
    
    # --- MÉTRICA NUEVA: Ventas / Dinero en comandas de hoy ---
    comandas_hoy = ConsumoMesa.objects.filter(mesa__reserva__fecha=hoy)
    ventas_totales_hoy = sum(c.subtotal() for c in comandas_hoy)

    # --- DATOS PARA GRÁFICO 1: Dona de Estados de Reservas de Hoy ---
    estados_conteo = reservas_hoy_qs.values('estado').annotate(total=Count('id'))
    estados_nombres = [item['estado'].capitalize() for item in estados_conteo]
    estados_valores = [item['total'] for item in estados_conteo]
    
    if not estados_nombres:
        estados_nombres = ['Sin reservas hoy']
        estados_valores = [0]

    # --- DATOS PARA GRÁFICO 2: Top Platos Más Solicitados ---
    top_platos = (
        ConsumoMesa.objects.values('plato__nombre')
        .annotate(total_cantidad=Sum('cantidad'))
        .order_by('-total_cantidad')[:5]
    )
    platos_labels = [p['plato__nombre'] if p['plato__nombre'] else 'Sin nombre' for p in top_platos]
    platos_data = [p['total_cantidad'] for p in top_platos]

    if not platos_labels:
        platos_labels = ['Sin datos aún']
        platos_data = [0]

    # --- DATOS PARA GRÁFICO 3 (NUEVO): Reservas por Zona del Restaurante ---
    reservas_por_zona = (
        reservas_hoy_qs.values('mesa__zona__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    zonas_labels = [z['mesa__zona__nombre'] if z['mesa__zona__nombre'] else 'General' for z in reservas_por_zona]
    zonas_data = [z['total'] for z in reservas_por_zona]

    if not zonas_labels:
        zonas_labels = ['Sin asignar']
        zonas_data = [0]

    contexto = {
        'reservas_hoy': reservas_hoy_qs.count(),
        'pendientes_hoy': reservas_hoy_qs.filter(estado__iexact='pendiente').count(),
        'confirmadas_hoy': reservas_hoy_qs.filter(estado__iexact='confirmada').count(),
        'ventas_totales_hoy': ventas_totales_hoy,
        'total_platos': Plato.objects.count(),
        'total_usuarios': Usuario.objects.count(),
        # Serialización segura a JSON para Chart.js
        'estados_nombres': json.dumps(estados_nombres),
        'estados_valores': json.dumps(estados_valores),
        'platos_labels': json.dumps(platos_labels),
        'platos_data': json.dumps(platos_data),
        'zonas_labels': json.dumps(zonas_labels),
        'zonas_data': json.dumps(zonas_data),
    }
    
    return render(request, 'landing/inicio_admin.html', contexto)