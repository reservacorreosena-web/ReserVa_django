from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='inicio'),
    path('perfil/', views.perfil_usuario, name='perfil'),

]
