from django.contrib import admin
from .models import  Plato
class Plato_admin(admin.ModelAdmin):
    search_fields = ('nombre','precio')
    list_filter = ('disponible',)
admin.site.register(Plato,Plato_admin)

