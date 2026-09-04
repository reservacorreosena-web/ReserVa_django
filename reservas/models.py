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

class Plato(models.Model):
    CATEGORIAS = [
        ('entradas', 'Entradas'),
        ('platos_fuertes', 'Platos Fuertes'),
        ('bebidas', 'Bebidas'),
        ('postres', 'Postres'),
        ('otros', 'Otros'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='platos_fuertes')
    disponible = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    imagen = models.ImageField(upload_to='platos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.get_categoria_display()}"


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

class ConsumoMesa(models.Model):
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    reserva = models.ForeignKey(Reserva, on_delete=models.SET_NULL, null=True, blank=True)
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, null=True, blank=True) # <--- Agrega null=True, blank=True
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    pagado = models.BooleanField(default=False)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"Mesa #{self.mesa.numero} - {self.cantidad}x {self.plato.nombre}"