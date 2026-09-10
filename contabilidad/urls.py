from django.urls import path
from . import views
from django.urls import path
from . import views

urlpatterns = [

    path('', views.inicio, name='inicio_contabilidad'),
    path('gastos/', views.control_gastos, name='control_gastos'),
    path('guardar_gasto/', views.guardar_gasto, name='guardar_gasto'),
    path('eliminar_gasto/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),
    path('editar_gasto/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('inicio_cierre_caja/', views.cierre_caja, name='inicio_cierre_caja'),
]