from django.urls import path
from . import views

urlpatterns = [
    path('crear_reserva/', views.crear_reserva, name='crear_reserva'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar_reserva/<int:id>/', views.cancelar_reserva, name='cancelar'),
    path('editar_reserva/<int:id>/', views.actualizar_reserva, name='actualizar'),
    path('confirmacion/', views.confirmacion, name='confirmacion'),
    path('historial_reservas/', views.historial_reservas, name='historial_reservas'),
    path('reserva/cambiar-estado/<int:id>/<str:nuevo_estado>/', views.cambiar_estado_reserva,
         name='cambiar_estado_reserva'),
    path('reservar/mapa/', views.seleccionar_mesa_mapa, name='seleccionar_mesa_mapa'),

    # Rutas del nuevo módulo POS / Vender (Administrador)
    path('admin/vender/', views.admin_mapa_mesas, name='admin_mapa_mesas'),
    path('admin/vender/mesa/<int:mesa_id>/', views.admin_detalle_mesa, name='admin_detalle_mesa'),
    path('admin/vender/mesa/<int:mesa_id>/agregar/<int:plato_id>/', views.admin_agregar_al_carrito,
         name='admin_agregar_al_carrito'),
    path('admin/vender/item/<int:consumo_id>/eliminar/', views.admin_eliminar_item_carrito,
         name='admin_eliminar_item_carrito'),
    path('admin/vender/mesa/<int:mesa_id>/cobrar/', views.admin_cobrar_mesa, name='admin_cobrar_mesa'),
    path('admin/vender/mesa/<int:mesa_id>/enviar-pedido/', views.admin_enviar_pedido, name='admin_enviar_pedido'),
]