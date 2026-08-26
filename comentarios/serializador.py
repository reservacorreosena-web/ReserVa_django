from .models import *
from rest_framework import serializers

class ResenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resena
        # fields = ['id', 'nombre', 'costo', 'descripcion', 'estado']
        fields = '__main__'
        fields = '__all__'