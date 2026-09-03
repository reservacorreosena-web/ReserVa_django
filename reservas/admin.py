from django.contrib import admin
from .models import Plato, Zona, Mesa, Reserva, ConsumoMesa  # Asegúrate de importar los nombres reales de tus modelos

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    search_fields = ('nombre', 'precio')
    list_filter = ('disponible',)

# Registra aquí los demás modelos para que vuelvan a aparecer en el menú lateral:
admin.site.register(Zona)
admin.site.register(Mesa)
admin.site.register(Reserva)
admin.site.register(ConsumoMesa) # (Ajusta los nombres según cómo se llamen exactamente en tu models.py de reservas)