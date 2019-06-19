from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from common.model_manager.marketer_manager import MarketerModelManager
import config


class MarketerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('Token') or request._request.META.get('HTTP_TOKEN')
        if token is None:
            raise exceptions.AuthenticationFailed()

        openid_session_unionid = cache.get(token)
        if openid_session_unionid is None:
            raise exceptions.AuthenticationFailed('Invalid token')
            # return None, None

        # get user
        marketer = MarketerModelManager()
        marketer = marketer.has_unionid(openid_session_unionid['unionid'])
        if marketer is None:
            return None, None
        elif marketer.status == config.SYSTEM_USER_STATUS.DISABLED:
            raise exceptions.AuthenticationFailed('Disabled User')
        return marketer, None


class MarketerRegisterAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('Token') or request._request.META.get('HTTP_TOKEN')
        if token is None:
            raise exceptions.AuthenticationFailed('Invalid token')

        id_session = cache.get(token)
        if id_session is None:
            raise exceptions.AuthenticationFailed('Invalid token')

        # get openid
        openid = id_session['openid']
        unionid = id_session['unionid']
        if openid is None:
            return None, None

        return dict(openid=openid, unionid=unionid), None
