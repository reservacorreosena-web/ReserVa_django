"""
URL configuration for ReserVa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import routers

from comentarios import views
from usuarios.views import UsuarioViewSet
router = routers.DefaultRouter()
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

#PRUEBAS MI PP


from django.contrib.auth.views import LogoutView


from comentarios.views import ResenaViewSet
from reservas.views import ReservaViewSet
from usuarios.views import UsuarioViewSet
from contabilidad.views import MovimientoViewSet

router.register('reservas', ReservaViewSet)
router.register('resenas', ResenaViewSet)
router.register('usuarios', UsuarioViewSet)
router.register('movimientos', MovimientoViewSet)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('reservas/', include('reservas.urls')),  # Esto conecta las URLs de la app reservas
    path('', include('landing.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('comentarios/', include('comentarios.urls')),
    path('menu/',include('menu.urls')),
    path('contabilidad/',include('contabilidad.urls')),

    #apis
    path('api/', include(router.urls)),

    #login apis
    path('api/auth/', include('rest_framework.urls')),

    #drf spectacular
    # 🚀 RUTAS PARA DRF-SPECTACULAR (DOCUMENTACIÓN)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    #URL DE TOKENS
    path('api/api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout'),
    

]