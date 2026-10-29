"""Reglas compartidas de disponibilidad de mesas.

La vista HTML del mapa y la API usan exactamente las mismas reglas:
una mesa está ocupada si tiene una reserva activa en la misma fecha/hora
o si tiene consumos pendientes de pago.
"""

from datetime import datetime

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import ConsumoMesa, Reserva

ESTADOS_RESERVA_ACTIVA = ("pendiente", "confirmada", "asistio")

MOTIVO_RESERVADA = "reservada"
MOTIVO_EN_CONSUMO = "en_consumo"
MOTIVO_CAPACIDAD = "capacidad"


def parse_fecha(valor):
    """Convierte ``YYYY-MM-DD`` en ``date`` y lanza ValidationError si no es válido."""
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError({"fecha": "Formato de fecha inválido. Usa YYYY-MM-DD."})


def parse_hora(valor):
    """Convierte ``HH:MM`` o ``HH:MM:SS`` en ``time``."""
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(str(valor), formato).time()
        except (TypeError, ValueError):
            continue
    raise ValidationError({"hora": "Formato de hora inválido. Usa HH:MM."})


def parse_fecha_hora(fecha, hora):
    if not fecha or not hora:
        raise ValidationError(
            {"detail": "Debes indicar la fecha y la hora de la reserva."}
        )
    return parse_fecha(fecha), parse_hora(hora)


def parse_personas(valor):
    """Valida la cantidad de personas con el mismo rango que el flujo web."""
    if valor in (None, ""):
        return None
    try:
        personas = int(valor)
    except (TypeError, ValueError):
        raise ValidationError({"personas": "Debe ser un número entero."})
    if personas < 1 or personas > 20:
        raise ValidationError({"personas": "Debe estar entre 1 y 20."})
    return personas


def obtener_ocupacion(fecha, hora, excluir_reserva_id=None):
    """Devuelve (mesas reservadas, mesas con consumo pendiente) para fecha/hora.

    ``excluir_reserva_id`` se usa al editar una reserva para que no se considere
    ocupada por sí misma.
    """
    reservas = Reserva.objects.filter(
        fecha=fecha,
        hora=hora,
        estado__in=ESTADOS_RESERVA_ACTIVA,
        mesa__isnull=False,
    )
    consumos = ConsumoMesa.objects.filter(pagado=False, mesa__isnull=False)

    if excluir_reserva_id is not None:
        reservas = reservas.exclude(pk=excluir_reserva_id)
        consumos = consumos.exclude(reserva_id=excluir_reserva_id)

    return (
        set(reservas.values_list("mesa_id", flat=True)),
        set(consumos.values_list("mesa_id", flat=True)),
    )


def evaluar_mesa(mesa, reservadas, consumos, personas=None):
    """Devuelve ``(disponible, motivo)`` para una mesa.

    El orden de prioridad es el mismo que muestra el mapa web: primero consumo
    activo, luego reserva en el horario y finalmente capacidad insuficiente.
    """
    if mesa.id in consumos:
        return False, MOTIVO_EN_CONSUMO
    if mesa.id in reservadas:
        return False, MOTIVO_RESERVADA
    if personas and mesa.capacidad < personas:
        return False, MOTIVO_CAPACIDAD
    return True, None


def validar_reserva_en_mesa(mesa, fecha, hora, personas, excluir_reserva_id=None):
    """Lanza ValidationError si la mesa no puede reservarse.

    Se usa tanto en la validación del serializer como dentro de la transacción
    de creación/edición.
    """
    if mesa is None:
        return

    reservadas, consumos = obtener_ocupacion(
        fecha, hora, excluir_reserva_id=excluir_reserva_id
    )
    disponible, motivo = evaluar_mesa(mesa, reservadas, consumos, personas)
    if disponible:
        return

    if motivo == MOTIVO_EN_CONSUMO:
        detalle = (
            f"La mesa #{mesa.numero} tiene un consumo activo pendiente de pago."
        )
    elif motivo == MOTIVO_RESERVADA:
        detalle = (
            f"La mesa #{mesa.numero} ya está reservada para esa fecha y hora."
        )
    else:
        detalle = (
            f"La mesa #{mesa.numero} tiene capacidad para {mesa.capacidad} "
            f"personas y la reserva es para {personas}."
        )

    raise ValidationError({"mesa": detalle})


def fecha_no_pasada(valor):
    if valor and valor < timezone.now().date():
        raise ValidationError(
            {"fecha": "No puedes realizar una reserva en una fecha pasada."}
        )
    return valor
