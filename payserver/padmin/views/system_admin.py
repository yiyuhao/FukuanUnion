from ipware import get_client_ip
from rest_framework import permissions, status, viewsets, views
from rest_framework.response import Response

from common.models import SystemAdmin
from padmin import utils
from padmin.auth import DefaultAuthMixin, admin_permissions
from padmin.serializers import SystemAdminSerializer, LoginSerializer
from padmin.paginations import ResultsSetPagination


class LoginView(DefaultAuthMixin, views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client_ip, _ = get_client_ip(request._request)
        serializer = LoginSerializer(client_ip=client_ip, data=request.data)
        serializer.is_valid(raise_exception=True)
        utils.login_user(self.request, serializer.user)
        output_serializer = SystemAdminSerializer(serializer.user)
        return Response(
            status=status.HTTP_200_OK,
            data=output_serializer.data
        )


class LogoutView(DefaultAuthMixin, views.APIView):
    def post(self, request):
        utils.logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(DefaultAuthMixin, views.APIView):
    def get(self, request):
        serializer = SystemAdminSerializer(request._user)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class SystemAdminViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = SystemAdmin.objects.filter(is_super=False).order_by('-id')
    serializer_class = SystemAdminSerializer
    permission_classes = (admin_permissions['PLATFORM_ADMIN'],)
    pagination_class = ResultsSetPagination


login = LoginView.as_view()
logout = LogoutView.as_view()
me = MeView.as_view()

system_admin_list = SystemAdminViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

system_admin_detail = SystemAdminViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})
