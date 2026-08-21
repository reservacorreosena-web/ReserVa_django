from django.contrib import admin
from .models import Movimiento
class Movimiento_Admin(admin.ModelAdmin):
    search_fields = ('concepto',)
admin.site.register(Movimiento,Movimiento_Admin)
