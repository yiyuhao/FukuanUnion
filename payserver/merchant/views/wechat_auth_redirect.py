#
#      File: wechat_auth_redirect.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging

from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from common.auth.wechat.web_auth import WeChantWebAuthHandler
from common.error_handler import MerchantError
from common.model_manager.merchant_admin_manager import MerchantAdminModelManager
from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES
from ws_service.utils import PublishToRedisChannel
from dynaconf import settings as dynasettings


logger = logging.getLogger(__name__)


class AddCashierCRCodeViewSet(GenericViewSet):
    @action(detail=False, url_name='wechat_auth_redirect')
    def wechat_auth_redirect(self, request):
        """
        扫码添加收银员 接收回调url的code和参数state, 这里state是channels_key
        """
        code = request.GET.get('code', '')
        state = request.GET.get('state', '')

        logger.info(f'try add a cashier by web socket: code({code}), state({state})')

        wechat_auth_handler = WeChantWebAuthHandler(
            app_id=dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MERCHANT,
            app_secret=dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_MERCHANT
        )
        access_token, openid = wechat_auth_handler.gen_access_token(code=code)
        user_info = wechat_auth_handler.gen_user_info(access_token, openid)

        user_info['channel_key'] = state

        logger.info(f'try add a cashier: {user_info}')

        # 将获取到的数据发送到 web socket
        res = PublishToRedisChannel.publish_to_channel(data=user_info)

        manager = MerchantAdminModelManager()
        cashier = manager.get_merchant_admin(user_info['unionid'])

        error = ''

        # 已添加该收银员或该收银员已绑定其他商铺
        if cashier and cashier.status == SYSTEM_USER_STATUS['USING']:
            error = f'{MerchantError.cashier_already_has_been_added["detail"]}' \
                    f'或{MerchantError.cashier_already_worked_in_another_merchant["detail"]}'

        # 商户管理员无法成为收银员
        if cashier and cashier.merchant_admin_type == MERCHANT_ADMIN_TYPES['ADMIN']:
            error = MerchantError.cashier_is_merchant_admin['detail']

        if res.get('message') == 'success' and not error:
            return render(request, 'auth_web/auth_ok.html', {
                'title': "添加收银员",
                'auth_type': "add_cashier",
            })
        else:
            return render(request, 'auth_web/auth_error.html', {
                'title': "添加收银员", 'info': error or "添加失败,请重试"})
