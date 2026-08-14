from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_platos_admin, name='ver_carta_admin'),
    path('crear_plato/', views.crear_plato, name='crear_plato'),
    path('eliminar_plato/<int:plato_id>/', views.eliminar_plato, name='eliminar_plato'),
    path('editar_plato/<int:id>/', views.editar_plato,name='editar_plato'),
    path('ver_carta',views.listar_platos, name='ver_carta')
]