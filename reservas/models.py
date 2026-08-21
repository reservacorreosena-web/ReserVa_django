from django.db import models

"""
class Zona(models.Model):
    ZONAS_DISPONIBLES = [
        ('salon', 'Salón Principal'),
        ('terraza', 'Terraza'),
        ('mirador', 'Mirador'),
    ]
    zona = models.CharField(max_length=20, choices=ZONAS_DISPONIBLES, default='salon')
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_zona_display()} - {self.descripcion or ''}"


class Mesa(models.Model):
    ESTADOS_MESA = [
        ('disponible', 'Disponible'),
        ('reservada', 'Reservada'),
        ('ocupada', 'Ocupada'),
    ]
    nombre = models.CharField(max_length=100)
    numero_mesa = models.IntegerField(unique=True)
    capacidad = models.IntegerField()
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE, related_name='mesas')
    estado = models.CharField(max_length=20, choices=ESTADOS_MESA, default='disponible')

    def __str__(self):
        return f"Mesa {self.numero_mesa} ({self.estado}) - {self.zona}"
"""


class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('asistio', 'Asistió'),
        ('cancelada', 'Cancelada'),
    ]
    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    hora = models.TimeField()
    cantidad_personas = models.PositiveIntegerField()
    telefono = models.CharField(max_length=20)

    # Campo de texto sencillo para evitar el ForeignKey
    mesa = models.CharField(max_length=50)

    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')

    def __str__(self):
        return f"{self.nombre} - {self.fecha} {self.hora}"