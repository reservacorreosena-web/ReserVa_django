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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from usuarios.views import api_login, api_me

urlpatterns = [
    path('admin/', admin.site.urls),
    path('reservas/', include('reservas.urls')),  # Esto conecta las URLs de la app reservas
    path('', include('landing.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('comentarios/', include('comentarios.urls')),
    path('menu/', include('menu.urls')),
    path('contabilidad/', include('contabilidad.urls')),

    # Autenticación API para Flutter
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/token/', obtain_auth_token, name='api_auth_token'),
    path('api/auth/login/', api_login, name='api_auth_login'),
    path('api/auth/me/', api_me, name='api_auth_me'),

    # 📚 Endpoints para la documentación de la API con drf-spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),


]
#Configuramos para que ReserVa admita imagenes
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)