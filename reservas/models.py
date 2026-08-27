from django.db import models
from usuarios.models import Usuario


class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('asistio', 'Asistió'),
        ('cancelada', 'Cancelada'),
    ]

    #Guarda la clave foranea, relaciona cada reserva con el usuario, guarda una columna llamada 'usuario_id'
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    fecha = models.DateField()
    hora = models.TimeField()
    cantidad_personas = models.PositiveIntegerField()

    # Campo temporal de mesa (mientras implementamos el mapa)
    mesa = models.CharField(max_length=50, blank=True, null=True, default="Por asignar")

    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')

    def __str__(self):
        return f"Reserva #{self.id} - {self.usuario.nombre} ({self.fecha})"