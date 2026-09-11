from email.policy import default

from django.db import models
from django.utils import timezone

class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso (+)'),
        ('GASTO', 'Gasto (-)'),
    ]

    CATEGORIA_CHOICES = [
        ('RESERVA', 'Consumo Reservas'),
        ('INSUMOS', 'Insumos / Alimentos'),
        ('SERVICIOS', 'Servicios Públicos'),
        ('NOMINA', 'Nómina / Personal'),
        ('OTROS', 'Otros Gastos'),




    ]

    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo (Caja)'),
        ('TRANSFERENCIA', 'Transferencia (Nequi/Bancolombia)'),
        ('TARJETA', 'Tarjeta Débito/Crédito'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='GASTO')
    concepto = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='OTROS')
    valor = models.IntegerField()
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES,)

    def __str__(self):
        return f"{self.tipo} - {self.concepto} (${self.valor})"

class Comentario_caja(models.Model):
    fecha = models.DateField(unique=True)
    comentario = models.TextField(max_length=500)

    def __str__(self):
        return f"Observación del {self.fecha}"