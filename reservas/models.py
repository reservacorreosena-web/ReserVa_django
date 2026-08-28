from django.db import models
from usuarios.models import Usuario

class Zona(models.Model):
    nombre = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre

class Mesa(models.Model):
    numero = models.IntegerField(unique=True)
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE)
    capacidad = models.IntegerField()
    posicion_x = models.IntegerField(default=0)
    posicion_y = models.IntegerField(default=0)

    def __str__(self):
        return f"Mesa {self.numero} (Cap: {self.capacidad})"

class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, null=True, blank=True)
    cantidad_personas = models.IntegerField()
    fecha = models.DateField()
    hora = models.TimeField()
    notas = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, default='pendiente')
    
    def __str__(self):
        return f"Reserva {self.usuario.nombre} - Mesa {self.mesa.numero if self.mesa else 'Sin asignar'}"