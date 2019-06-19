#      File: auth.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/22
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from common.error_handler import MerchantError
from common.model_manager.merchant_admin_manager import MerchantAdminModelManager
from config import MerchantMiniProgram, SYSTEM_USER_STATUS


class MerchantAdminAuthentication(BaseAuthentication):
    """merchant_admin or cashier"""

    def authenticate(self, request):
        token = request._request.META.get('HTTP_TOKEN') or request.META.get('Token')
        if token is None:
            raise exceptions.AuthenticationFailed(MerchantError.no_token['detail'])

        wechat_auth_data = cache.get(token)  # openid, unionid, session_key
        if wechat_auth_data is None:
            raise exceptions.AuthenticationFailed(MerchantError.invalid_token['detail'])

        # refresh token expiration time
        cache.set(token, wechat_auth_data, MerchantMiniProgram.user_token_expiration_time)

        # get user
        manager = MerchantAdminModelManager()
        merchant_admin = manager.get_merchant_admin(wechat_auth_data['unionid'])
        if merchant_admin is None:
            raise exceptions.AuthenticationFailed(MerchantError.invalid_user['detail'])

        # disabled user
        elif merchant_admin.status == SYSTEM_USER_STATUS.DISABLED:
            raise exceptions.AuthenticationFailed(MerchantError.disabled_user)
        return merchant_admin, None
