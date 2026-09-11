from django.contrib import admin
from .models import Movimiento, Comentario_caja

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    search_fields = ('concepto',)

@admin.register(Comentario_caja)
class ComentarioCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'comentario')