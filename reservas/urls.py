from django.urls import path
from . import views



urlpatterns = [
    path('crear_reserva/', views.crear_reserva, name='crear_reserva'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar_reserva/<int:id>/', views.cancelar_reserva, name='cancelar'),
    path('editar_reserva/<int:id>/', views.actualizar_reserva, name='actualizar'),
    path('confirmacion/', views.confirmacion,name='confirmacion'),
    path('historial_reservas/', views.historial_reservas,name='historial_reservas'),
    path('reserva/cambiar-estado/<int:id>/<str:nuevo_estado>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('reservar/mapa/', views.seleccionar_mesa_mapa, name='seleccionar_mesa_mapa'),
    path('admin/mapa/', views.admin_mapa_mesas, name='admin_mapa_mesas'),
    path('admin/mesa/<int:mesa_id>/comanda/', views.admin_agregar_consumo, name='admin_agregar_consumo'),
    path('admin/mesa/<int:mesa_id>/cerrar/', views.admin_cerrar_mesa, name='admin_cerrar_mesa'),
]
