from django.db import transaction
from rest_framework import serializers

from .disponibilidad import (
    fecha_no_pasada,
    validar_reserva_en_mesa,
)
from .models import Mesa, Reserva


class ReservaSerializer(serializers.ModelSerializer):
    """Serializer de reservas para la API.

    ``usuario`` y ``estado`` son de solo lectura: el propietario se obtiene del
    token y el estado inicial siempre es ``pendiente``. Así se evita que un
    cliente cree reservas a nombre de otra persona o que se asigne estados
    administrativos.
    """

    usuario = serializers.PrimaryKeyRelatedField(read_only=True)
    estado = serializers.CharField(read_only=True)
    mesa_numero = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            "id",
            "usuario",
            "mesa",
            "mesa_numero",
            "cantidad_personas",
            "fecha",
            "hora",
            "notas",
            "estado",
        ]

    def get_mesa_numero(self, obj) -> int | None:
        return obj.mesa.numero if obj.mesa_id else None

    def validate_cantidad_personas(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError(
                "La cantidad de personas debe estar entre 1 y 20."
            )
        return value

    def validate_fecha(self, value):
        return fecha_no_pasada(value)

    def validate(self, attrs):
        instancia = self.instance
        personas = attrs.get(
            "cantidad_personas",
            getattr(instancia, "cantidad_personas", None),
        )
        fecha = attrs.get("fecha", getattr(instancia, "fecha", None))
        hora = attrs.get("hora", getattr(instancia, "hora", None))
        mesa = attrs.get("mesa", getattr(instancia, "mesa", None))

        if mesa is not None and personas and mesa.capacidad < personas:
            raise serializers.ValidationError(
                {
                    "mesa": (
                        f"La mesa #{mesa.numero} tiene capacidad para "
                        f"{mesa.capacidad} personas y la reserva es para "
                        f"{personas}."
                    )
                }
            )

        if mesa is not None and fecha and hora:
            validar_reserva_en_mesa(
                mesa,
                fecha,
                hora,
                personas,
                excluir_reserva_id=getattr(instancia, "pk", None),
            )

        return attrs

    def create(self, validated_data):
        # Se bloquea la fila de la mesa y se repite la comprobación dentro de la
        # transacción para reducir el riesgo de doble reserva por concurrencia.
        with transaction.atomic():
            mesa = validated_data.get("mesa")
            if mesa is not None:
                Mesa.objects.select_for_update().get(pk=mesa.pk)
                validar_reserva_en_mesa(
                    mesa,
                    validated_data["fecha"],
                    validated_data["hora"],
                    validated_data["cantidad_personas"],
                )
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            mesa = validated_data.get("mesa", instance.mesa)
            if mesa is not None:
                Mesa.objects.select_for_update().get(pk=mesa.pk)
                validar_reserva_en_mesa(
                    mesa,
                    validated_data.get("fecha", instance.fecha),
                    validated_data.get("hora", instance.hora),
                    validated_data.get(
                        "cantidad_personas", instance.cantidad_personas
                    ),
                    excluir_reserva_id=instance.pk,
                )
            return super().update(instance, validated_data)
