# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny

from common.error_handler import raise_with_code
from common.models import Client
from puser import consts
from puser import error_codes


class TokenAuthenticationBase(BaseAuthentication):

    def get_client(self, token_session, empty_allowed=False):
        try:
            client_id = token_session[consts.client_session_key]
        except KeyError:  # token过期已从cache中删除
            if empty_allowed:
                return None
            else:
                raise_with_code(
                    exceptions.AuthenticationFailed(),
                    error_codes.auth_failed_token_expired)

        try:
            client = Client.objects.get(pk=client_id)
        except Client.DoesNotExist:  # token无效
            token_session.delete()
            raise_with_code(exceptions.AuthenticationFailed(),
                            error_codes.auth_failed_token_invalid)

        return client

    def authenticate(self, request):
        raise NotImplementedError


class EmptyAllowedTokenAuthentication(TokenAuthenticationBase):
    """Allow auth when token_session empty"""

    def authenticate(self, request):
        token_session = request.token_session
        token_session.set_namespace(consts.token_namespace)

        if token_session.is_empty():
            return None, None

        client = self.get_client(token_session, empty_allowed=True)

        return client, token_session.token


class EmptyDeniedTokenAuthentication(TokenAuthenticationBase):
    """Deny auth when token_session empty"""

    def authenticate(self, request):
        token_session = request.token_session
        token_session.set_namespace(consts.token_namespace)

        if request._request.method == 'OPTIONS':
            return '', ''

        if token_session.is_empty():  # token没有上报
            raise_with_code(exceptions.NotAuthenticated(),
                            error_codes.auth_failed_token_missing)  # 401

        client = self.get_client(token_session)

        return client, token_session.token


class BasicTokenAuthMixin:
    authentication_classes = (EmptyDeniedTokenAuthentication,)
    permission_classes = (AllowAny,)


class EmptyAllowedTokenAuthMixin:
    authentication_classes = (EmptyAllowedTokenAuthentication,)
    permission_classes = (AllowAny,)
