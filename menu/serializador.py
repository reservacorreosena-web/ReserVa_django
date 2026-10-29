from rest_framework import serializers

from reservas.disponibilidad import evaluar_mesa
from reservas.models import Mesa, Plato, Zona


class PlatoSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(
        source="get_categoria_display", read_only=True
    )

    class Meta:
        model = Plato
        fields = [
            "id",
            "nombre",
            "descripcion",
            "precio",
            "categoria",
            "categoria_display",
            "disponible",
            "destacado",
            "imagen",
            "stock",
        ]


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = ["id", "nombre"]


class MesaSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.SerializerMethodField()
    disponible = serializers.SerializerMethodField()
    motivo_no_disponible = serializers.SerializerMethodField()

    class Meta:
        model = Mesa
        fields = [
            "id",
            "numero",
            "capacidad",
            "forma",
            "zona",
            "zona_nombre",
            "posicion_x",
            "posicion_y",
            "disponible",
            "motivo_no_disponible",
        ]

    def _evaluar(self, obj):
        info = self.context.get("disponibilidad")
        if not info:
            return None, None
        return evaluar_mesa(
            obj,
            info["reservadas"],
            info["consumos"],
            info["personas"],
        )

    def get_zona_nombre(self, obj) -> str | None:
        return obj.zona.nombre if obj.zona_id else None

    def get_disponible(self, obj) -> bool | None:
        disponible, _ = self._evaluar(obj)
        return disponible

    def get_motivo_no_disponible(self, obj) -> str | None:
        _, motivo = self._evaluar(obj)
        return motivo
