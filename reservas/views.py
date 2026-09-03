from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reserva, Mesa, Zona, Plato, ConsumoMesa
from usuarios.models import Usuario
from usuarios.decorador import verificar, solo_admin
from django.db.models import Q
from .utils import enviar_correo_reserva


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

    # 1. Mesas ocupadas por otras reservas en esa fecha y hora
    mesas_por_reserva_ids = Reserva.objects.filter(
        fecha=fecha,
        hora=hora,
        estado__in=['pendiente', 'confirmada', 'asistio']
    ).values_list('mesa_id', flat=True)

    # 2. Mesas que tienen un consumo activo en este preciso momento (en el POS / presenciales)
    mesas_con_consumo_ids = ConsumoMesa.objects.filter(pagado=False).values_list('mesa_id', flat=True)

    # 3. Unimos ambos grupos para bloquearlas en el mapa de reservas
    mesas_ocupadas_ids = set(list(mesas_por_reserva_ids) + list(mesas_con_consumo_ids))

    todas_las_mesas = Mesa.objects.all()

    if request.method == "POST":
        mesa_id = request.POST.get("mesa_id")
        
        # Validación extra por seguridad por si intentan forzar una mesa ocupada
        if int(mesa_id) in mesas_ocupadas_ids:
            messages.error(request, "Lo sentimos, esta mesa acaba de ser ocupada o tiene un consumo activo.")
            return redirect('seleccionar_mesa_mapa')

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
    reservas = Reserva.objects.all().order_by('-fecha', '-hora')

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


# --- MÓDULO POS / ADMIN VENTAS ---

@solo_admin  # O @verificar, dependiendo de cómo protejas esta vista en tu proyecto
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

    # NUEVO: Calculamos el total de consumo activo por cada mesa
    consumos_activos = ConsumoMesa.objects.filter(pagado=False)
    
    # Creamos un diccionario { mesa_id: total_cuenta }
    totales_consumo = {}
    mesas_con_consumo = set()
    
    for consumo in consumos_activos:
        mesas_con_consumo.add(consumo.mesa_id)
        # Si la mesa ya tiene un total sumado, le acumulamos el subtotal, sino lo iniciamos
        totales_consumo[consumo.mesa_id] = totales_consumo.get(consumo.mesa_id, 0) + consumo.subtotal()

    contexto = {
        'mesas': todas_las_mesas,
        'mapa_reservas': mapa_reservas,
        'mesas_con_consumo': mesas_con_consumo,
        'totales_consumo': totales_consumo, # <--- Pasamos este diccionario al template
        'fecha': fecha,
        'hora': hora,
    }
    return render(request, 'reservas/admin_mapa.html', contexto)


def admin_detalle_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)

    consumos = ConsumoMesa.objects.filter(mesa=mesa, pagado=False).select_related('plato')
    total_cuenta = sum(c.subtotal() for c in consumos)

    query = request.GET.get('q', '').strip()
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


def admin_enviar_pedido(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    consumos_nuevos = ConsumoMesa.objects.filter(mesa=mesa, pagado=False)
    
    if consumos_nuevos.exists():
        messages.success(request, f"¡Pedido enviado a cocina para la Mesa #{mesa.numero}!")
    else:
        messages.warning(request, "No hay platos agregados en la comanda actual.")
        
    return redirect('admin_detalle_mesa', mesa_id=mesa_id)