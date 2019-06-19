from rest_framework import permissions, exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck

import config


class AdminAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if 'admin' not in request._request.session:
            return None, None

        self.enforce_csrf(request)

        return request._request.session['admin'], None

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CSRFCheck().process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class AdminLoggedIn(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user is not None


class SuperAdminLoggedIn(permissions.BasePermission):
    message = "没有超级管理员权限"
    def has_permission(self, request, view):
        if request.user is None:
            return None
        return request.user.is_super

def create_permission_class(required_permission):
    def has_permission(self, request, view):
        if request.user is None:
            return False
        if request.user.is_super:
            return True
        user_permissions = request.user.permissions.split(',')
        return self.required_permission in user_permissions

    return type('AdminPermission_' + required_permission,
                (permissions.BasePermission,),
                dict(required_permission=required_permission,
                     has_permission=has_permission))


admin_permissions = {p: create_permission_class(p) for p in config.ADMIN_PERMISSIONS.keys()}


class DefaultAuthMixin(object):
    authentication_classes = (AdminAuthentication,)
    permission_classes = (AdminLoggedIn,)
