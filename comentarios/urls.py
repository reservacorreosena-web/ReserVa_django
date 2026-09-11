from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
app_name = 'comentarios'

router = DefaultRouter()
router.register(r'api/resenas', views.ResenaViewSet, basename='api-resenas')

urlpatterns = [
    path('comentarios/', views.crear_resena, name='crear_resena'),
    
    path('', include(router.urls)),
]
