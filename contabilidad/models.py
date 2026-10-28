from email.policy import default

from django.db import models
from django.utils import timezone


class SesionCaja(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    ]

    usuario_apertura = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_abiertas'
    )
    usuario_cierre = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_cerradas'
    )
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_gastos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_esperado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dinero_real = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='ABIERTA')

    class Meta:
        ordering = ['-fecha_apertura']
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'

    def __str__(self):
        return f"Caja #{self.id} ({self.estado}) - Apertura: {self.fecha_apertura.strftime('%Y-%m-%d %H:%M')}"


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
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    sesion_caja = models.ForeignKey(
        SesionCaja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos'
    )

    def __str__(self):
        return f"{self.tipo} - {self.concepto} (${self.valor})"


class Comentario_caja(models.Model):
    fecha = models.DateField(unique=True)
    comentario = models.TextField(max_length=500)

    def __str__(self):
        return f"Observación del {self.fecha}"