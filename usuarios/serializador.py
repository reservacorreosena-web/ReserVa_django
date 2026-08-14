from .models import *
from rest_framework import serializers

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        # fields = ['id', 'nombre', 'costo', 'descripcion', 'estado']
        fields = '__all__'