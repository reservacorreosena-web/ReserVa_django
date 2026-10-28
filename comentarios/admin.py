from django.contrib import admin
from .models import Resena

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'calificacion_comida', 'calificacion_servicio', 'fecha')
    list_filter = ('calificacion_comida', 'calificacion_servicio', 'fecha')
    search_fields = ('usuario__username', 'comentario')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
