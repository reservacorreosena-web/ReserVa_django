from django.contrib import admin
from .models import Plato, Zona, Mesa, Reserva, ConsumoMesa  # Asegúrate de importar los nombres reales de tus modelos

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    search_fields = ('nombre', 'precio')
    list_filter = ('disponible',)

# Registramos Zona y Mesa de forma limpia con @admin.register para poder filtrar las mesas por zona y forma fácilmente:
@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_filter = ('zona', 'forma')
    search_fields = ('numero',)

# Dejamos estos tal cual los tenías con site.register para no tocar su lógica interna
admin.site.register(Reserva)
admin.site.register(ConsumoMesa)