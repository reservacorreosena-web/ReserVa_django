from email.policy import default

from django.db import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=100)
    contraseña = models.CharField(max_length=255)
    rol = models.CharField(max_length=50, default='cliente')
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.email} ({self.rol})"

