from django.contrib import admin
from .models import Reserva,Mesa,Zona



class ZonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_zona_display', 'descripcion')

class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero_mesa', 'nombre', 'capacidad', 'zona', 'estado')
    #Crea una lista para filtrar con desplegables
    list_filter = ('zona', 'estado')
    #Esto activa un buscador
    search_fields = ('numero_mesa', 'nombre')

class ReservaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'hora', 'cantidad_personas', 'mesa', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('nombre', 'telefono')

admin.site.register(Reserva)
admin.site.register(Mesa)
admin.site.register(Zona)