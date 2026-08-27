from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reserva
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

        # 3. Crear y guardar la reserva vinculada a la instancia de Usuario
        nueva_reserva = Reserva.objects.create(
            usuario=usuario_instancia,
            cantidad_personas=personas,
            fecha=fecha_reserva_dt.date(),
            hora=fecha_reserva_dt.time(),
            notas=notas,
            estado='pendiente'
        )

        # 4. Enviar correo de confirmación
        try:
            enviar_correo_reserva(nueva_reserva)
        except Exception as e:
            print(f"Error al enviar el correo de confirmación: {e}")

        messages.success(request, "¡Tu mesa ha sido reservada con éxito!")
        return redirect('mis_reservas')

    return render(request, "reservas/formulario_reserva.html")


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
  filtro_estado = request.GET.get('filtro_estado')  # <--- Corregido 'filtro_estado'
  filtro_fecha = request.GET.get('filtro_fecha')


  if busqueda:
    reservas = reservas.filter(
        # __ Es para busquedas avanzadas, salta de tabla en tabla buscando llaves foraneas
        # icontains; si contiene el texto en mayuscula o minuscula lo pinta
        # si el id que contiene el input de busqueda... Si contiene usuario, nombre del input de busqueda..
        # Q es para hacer busquedas combinadas
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
    #Buscamos la reserva en la base de datos
    reservas = get_object_or_404(Reserva, id=id)
    #verificamos los estados validos de la reserva
    estados_valido = ['asistio', 'pendiente', 'cancelada', 'confirmada']
    # Validamos si el estado que mandaron por el botón está dentro de los permitidos
    if nuevo_estado in estados_valido:

        reservas.estado = nuevo_estado #Cambiamos el viejo estado por el nuevo
        reservas.save() # lo guardamos
        messages.success(request, f"La reserva #{reservas.id} ha sido actualizada")
    else:
        messages.error(request, "Estado no válido.")

    return redirect('historial_reservas')