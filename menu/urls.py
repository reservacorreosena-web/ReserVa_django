from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/platos', views.PlatoViewSet, basename='api-platos')
router.register(r'api/zonas', views.ZonaViewSet, basename='api-zonas')
router.register(r'api/mesas', views.MesaViewSet, basename='api-mesas')

urlpatterns = [
    path('', views.listar_platos_admin, name='ver_carta_admin'),
    path('crear_plato/', views.crear_plato, name='crear_plato'),
    path('eliminar_plato/<int:plato_id>/', views.eliminar_plato, name='eliminar_plato'),
    path('editar_plato/<int:id>/', views.editar_plato, name='editar_plato'),
    path('ver_carta/', views.listar_platos, name='ver_carta'),
    path('', include(router.urls)),
]
