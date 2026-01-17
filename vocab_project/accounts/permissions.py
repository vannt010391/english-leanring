from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Permission class that allows only admin users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsLearner(BasePermission):
    """Permission class that allows only learner users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_learner()


class IsAdminOrReadOnly(BasePermission):
    """Permission class that allows admin full access, others read-only."""

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsOwnerOrAdmin(BasePermission):
    """Permission class that allows owners or admins to access."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False
