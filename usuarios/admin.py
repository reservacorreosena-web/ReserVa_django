from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class Usuarios_admin(admin.ModelAdmin):
    list_filter = ('estado', 'rol')
    search_fields = ('nombre', 'email')
    list_display = ('nombre', 'email', 'rol', 'estado')
    readonly_fields = ('contraseña',)
