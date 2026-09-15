from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Creamos el router de DRF para la app contabilidad
router = DefaultRouter()
router.register(r'api/movimientos', views.MovimientoViewSet, basename='api-movimientos')
router.register(r'api/comentarios-caja', views.ComentarioCajaViewSet, basename='api-comentarios-caja')

urlpatterns = [
    # Rutas tradicionales HTML
    path('', views.inicio, name='inicio_contabilidad'),
    path('gastos/', views.control_gastos, name='control_gastos'),
    path('guardar_gasto/', views.guardar_gasto, name='guardar_gasto'),
    path('eliminar_gasto/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),
    path('editar_gasto/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('inicio_cierre_caja/', views.cierre_caja, name='inicio_cierre_caja'),
    path('comentario_caja/', views.comentario_caja, name='comentario_caja'),
    
    # Inclusión de las rutas de la API REST
    path('', include(router.urls)),
]