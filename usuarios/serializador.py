from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "estado", "contraseña"]
        extra_kwargs = {
            "contraseña": {"write_only": True},
        }


class RegistroSerializer(serializers.Serializer):
    """Datos de registro para la API (JSON).

    Acepta ``password`` y, por compatibilidad con el formulario web,
    también ``contraseña``. La contraseña siempre se guarda hasheada.
    """

    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(
        write_only=True, min_length=8, max_length=128
    )

    def to_internal_value(self, data):
        if "password" not in data and "contraseña" in data:
            data = data.copy()
            data["password"] = data.get("contraseña")
        return super().to_internal_value(data)

    def validate_nombre(self, value):
        nombre = value.strip().title()
        if len(nombre) < 2:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 2 caracteres."
            )
        return nombre

    def validate_email(self, value):
        email = value.strip().lower()
        if Usuario.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "Este correo ya se encuentra registrado."
            )
        return email

    def create(self, validated_data):
        return Usuario.objects.create(
            nombre=validated_data["nombre"],
            email=validated_data["email"],
            contraseña=make_password(validated_data["password"]),
            rol="cliente",
        )


class LoginSerializer(serializers.Serializer):
    """Credenciales documentadas para POST /api/auth/login/.

    La vista también acepta los alias ``username``/``correo`` y
    ``contraseña``/``clave`` por compatibilidad con clientes existentes.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UsuarioAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "estado"]


class AuthResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UsuarioAppSerializer()


class MeResponseSerializer(serializers.Serializer):
    user = UsuarioAppSerializer()
