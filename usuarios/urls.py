from django.urls import path
from . import views

urlpatterns = [
    path('iniciar_sesion/', views.inicio_sesion, name='iniciar_sesion'),
    path('registrarse/', views.crear_usuario, name='crear_usuario'),
    path('cerrar_sesion/', views.logout, name='cerrar_sesion'),
    path('listar_clientes/', views.mostrar_usuarios, name='listado_general'),
    path('usuarios/cambiar-estado/<int:usuario_id>/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),

    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    # ==========================================
    # RUTAS DE RECUPERACIÓN DE CONTRASEÑA (CUSTOM)
    # ==========================================
    path('recuperar-contrasena/', views.recuperar_contrasena_custom, name='password_reset'),
    path('recuperar-contrasena/enviado/', views.password_reset_done_view, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.reset_confirm_custom, name='password_reset_confirm'),
    path('reset/hecho/', views.password_reset_complete_view, name='password_reset_complete'),
]