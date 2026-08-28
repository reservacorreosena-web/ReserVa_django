from os import name

from django.urls import path
from . import views


urlpatterns = [
    path('iniciar_sesion/', views.inicio_sesion, name='iniciar_sesion'),
    path('registrarse/', views.crear_usuario, name='crear_usuario'),
    path('cerrar_sesion/', views.logout, name='cerrar_sesion'),
    path('listar_clientes/', views.mostrar_usuarios, name='listado_general'),
    path('usuarios/cambiar-estado/<int:usuario_id>/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),

    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
]
