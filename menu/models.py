from django.db import models

class Plato(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=400, blank=True, null=True)
    precio = models.IntegerField()
    disponible = models.BooleanField(default=True)
    categoria = models.CharField(max_length=50, default='plato_fuerte')
    destacado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre