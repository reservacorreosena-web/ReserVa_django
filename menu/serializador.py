from rest_framework import serializers

from reservas.models import Plato, Zona, Mesa


class PlatoSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = Plato
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'categoria',
            'categoria_display', 'disponible', 'destacado', 'imagen', 'stock',
        ]


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = ['id', 'nombre']


class MesaSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source='zona.nombre', read_only=True)

    class Meta:
        model = Mesa
        fields = ['id', 'numero', 'capacidad', 'forma', 'zona', 'zona_nombre']
