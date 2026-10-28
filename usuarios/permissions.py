from rest_framework import permissions

from usuarios.models import Usuario


def get_usuario_app(user):
    if not user or not user.is_authenticated:
        return None
    email = getattr(user, 'email', '') or getattr(user, 'username', '')
    if not email:
        return None
    return Usuario.objects.filter(email=email).first()


class IsUsuarioAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        usuario = get_usuario_app(request.user)
        if usuario and usuario.rol == 'admin':
            return True
        return bool(request.user.is_staff or request.user.is_superuser)


class IsUsuarioAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        usuario = get_usuario_app(request.user)
        if usuario and usuario.rol == 'admin':
            return True
        return bool(request.user.is_staff or request.user.is_superuser)


class IsOwnerOrUsuarioAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        usuario = get_usuario_app(request.user)
        if usuario and usuario.rol == 'admin':
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Reserva
        if hasattr(obj, 'usuario'):
            owner = obj.usuario
            if usuario and owner and getattr(owner, 'id') == getattr(usuario, 'id'):
                return True
            if hasattr(owner, 'email') and owner.email == request.user.email:
                return True
            if owner == request.user:
                return True

        # Resena (auth.User)
        if hasattr(obj, 'usuario') and isinstance(obj.usuario, type(request.user)):
            return obj.usuario_id == request.user.id

        return request.method in permissions.SAFE_METHODS
