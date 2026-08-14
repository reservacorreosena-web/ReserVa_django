from .models import *
from rest_framework import serializers
class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        # fields = ['id', 'nombre', 'costo', 'descripcion', 'estado']
        fields = '__all__'