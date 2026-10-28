from django.contrib import admin
from .models import Movimiento, Comentario_caja, SesionCaja

@admin.register(SesionCaja)
class SesionCajaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'estado', 'fecha_apertura', 'fecha_cierre',
        'saldo_inicial', 'total_ventas', 'total_gastos',
        'balance_esperado', 'dinero_real', 'diferencia'
    )
    list_filter = ('estado', 'fecha_apertura')
    search_fields = ('id', 'observaciones')
    readonly_fields = ('fecha_apertura',)

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'concepto', 'categoria', 'valor', 'metodo_pago', 'fecha', 'hora')
    list_filter = ('tipo', 'categoria', 'metodo_pago', 'fecha')
    search_fields = ('concepto',)
    ordering = ('-fecha', '-hora')

@admin.register(Comentario_caja)
class ComentarioCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'comentario')
    search_fields = ('comentario',)
    ordering = ('-fecha',)
