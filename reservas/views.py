from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reserva
from usuarios.models import Usuario
from usuarios.decorador import verificar, solo_admin


@verificar
def crear_reserva(request):
    if request.method == "POST":
        # Verifica las credencias del usuario logueado
        usuario_session = request.session.get('logueado')
        #le sacamos el ID para buscarlo en la BD y asignarlo como dueño de la reserva
        usuario_id = usuario_session.get('id')
        #Hace una consulta en la base de datos usando su ID
        usuario_instancia = get_object_or_404(Usuario, id=usuario_id)

        # 2. Capturamos únicamente los datos del nuevo formulario
        cantidad_personas = request.POST.get("cantidad_personas", "").strip()
        fecha = request.POST.get("fecha", "").strip()
        hora = request.POST.get("hora", "").strip()
        notas = request.POST.get("notas", "").strip()
        preordenar = request.POST.get("preordenar", "NO")
        # Creamos un contexto para que lo pasemos si el usuario llega a equivocarse llenando los datos y no los tenga que llenar de 0
        datos_formulario = {
            "cantidad_personas" : cantidad_personas,
            "fecha" : fecha,
            "hora":hora,
            "notas":notas
        }

        # --- VALIDACIONES DE NEGOCIO ---
        # Validar campos obligatorios
        if not cantidad_personas or not fecha or not hora:
            messages.error(request, "Por favor completa la cantidad de personas, fecha y hora.")
            return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})

        # Validar número de personas
        try:
            personas = int(cantidad_personas)
            if personas <= 0:
                messages.error(request, "La cantidad de personas debe ser mayor a 0.")
                return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})
            if personas > 20:
                messages.warning(request, "Las reservas no pueden superar las 20 personas.")
                return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})
        except ValueError:
            messages.error(request, "Ingresa un número válido para las personas.")
            return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})

        # Validar que la fecha/hora no sea en el pasado
        try:
            fecha_reserva = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            if fecha_reserva < datetime.now():
                messages.error(request, "No puedes realizar una reserva para una fecha u hora pasadas.")
                return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})
        except ValueError:
            messages.error(request, "El formato de fecha u hora es inválido.")
            return render(request, 'reservas/formulario_reserva.html', {"datos":datos_formulario})


        if preordenar == 'SI':
            # Guardamos los datos de la reserva en la sesión para completar con la carta
            request.session['datos_reserva_temporal'] = {
                'usuario_id': usuario_id,
                'cantidad_personas': personas,
                'fecha': fecha,
                'hora': hora,
                'notas': notas
            }
            return redirect('ver_carta')

        # Crear y guardar la reserva vinculada al usuario
        nueva_reserva = Reserva.objects.create(
            usuario=usuario_instancia,
            cantidad_personas=personas,
            fecha=fecha,
            hora=hora,
            notas=notas,
            estado='pendiente'
        )

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
    reservas = Reserva.objects.all().order_by('-id')

    total_reservas = reservas.count()
    confirmadas = reservas.filter(estado__iexact='confirmada').count()
    pendientes = reservas.filter(estado__iexact='pendiente').count()

    contexto = {
        'reservas': reservas,
        'total_reservas': total_reservas,
        'confirmadas': confirmadas,
        'pendientes': pendientes,
    }
    return render(request, 'reservas/historial_reservas.html', contexto)