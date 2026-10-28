from django.contrib import admin
from .models import Plato, Zona, Mesa, Reserva, ConsumoMesa

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'disponible', 'destacado')
    search_fields = ('nombre',)
    list_filter = ('categoria', 'disponible', 'destacado')
    list_editable = ('precio', 'stock', 'disponible')

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'capacidad', 'zona', 'forma', 'posicion_x', 'posicion_y')
    list_filter = ('zona', 'forma')
    search_fields = ('numero',)
    list_editable = ('capacidad', 'zona', 'forma')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'mesa', 'fecha', 'hora', 'cantidad_personas', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__nombre', 'usuario__email', 'id')
    list_editable = ('estado',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha', '-hora')

@admin.register(ConsumoMesa)
class ConsumoMesaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'reserva', 'plato', 'cantidad', 'precio_unitario', 'pagado', 'fecha_hora')
    list_filter = ('pagado', 'fecha_hora')
    search_fields = ('mesa__numero', 'plato__nombre')
