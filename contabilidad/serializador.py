from .models import *
from rest_framework import serializers

class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = '__all__'

class ComentarioCajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comentario_caja
        fields = '__all__'