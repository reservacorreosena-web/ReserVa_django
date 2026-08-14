from .models import *
from rest_framework import serializers

class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        # fields = ['id', 'nombre', 'costo', 'descripcion', 'estado']
        fields = '__all__'