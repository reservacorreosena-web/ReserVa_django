from django.urls import path
from . import views



urlpatterns = [
    path('crear_reserva/', views.crear_reserva, name='crear_reserva'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar_reserva/<int:id>/', views.cancelar_reserva, name='cancelar'),
    path('editar_reserva/<int:id>/', views.actualizar_reserva, name='actualizar'),
    path('confirmacion/', views.confirmacion,name='confirmacion'),
    path('historial_reservas/', views.historial_reservas,name='historial_reservas'),
]
