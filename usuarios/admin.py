from django.contrib import admin
from .models import Usuario

# Register your models here.

class Usuarios_admin(admin.ModelAdmin):
    list_filter = ('estado',)
    search_fields = ('usuario','email')



admin.site.register(Usuario, Usuarios_admin)
