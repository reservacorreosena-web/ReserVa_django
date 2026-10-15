from .models import *
from rest_framework import serializers

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'email', 'rol', 'estado', 'contraseña']
        extra_kwargs = {
            'contraseña': {'write_only': True}
        }