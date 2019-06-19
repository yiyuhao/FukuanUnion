# -*- coding: utf-8 -*-
#       File: web_auth.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-9-17
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
import requests
from dynaconf import settings as dynasettings
from urllib.parse import urlencode

from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.doclink.alipay_apis import AlipayApis

logger = logging.getLogger(__name__)


class AuthCodeError(Exception):
    def __init__(self, e, msg='auth code error'):
        logger.info(f'Alipay auth code error: {e}')
        super().__init__(msg)


class AlipayWebAuthHandler(object):
    """ alipay网页授权 """
    alipay_app_id = dynasettings.ALIPAY_APP_ID
    alipay_private_key = dynasettings.ALIPAY_APP_PRIVATE_KEY
    alipay_public_key = dynasettings.ALIPAY_PUBLIC_KEY

    def __init__(self):
        self.alipay_api_instance = AlipayApis(self.alipay_app_id,
                                              self.alipay_private_key,
                                              self.alipay_public_key)

    def gen_alipay_access_token(self, code):
        """根据code生成access_token

        Args:
            code (str): 授权时临时生成的code
        """
        try:
            auth_resp = self.alipay_api_instance.exchange_access_token(code)
            access_token = auth_resp.get('access_token')

        except (ApiRequestError, ApiReturnedError, KeyError) as e:
            raise AuthCodeError(e)

        return access_token

    def gen_alipay_user_info(self, access_token):
        """根据access_token获取用户信息

        Args:
            access_token (str): 用户授权的后生成的access_token
        """
        biz_content = dict(
            auth_token=access_token,
            scope='auth_user,auth_base',
            grant_type='authorization_code'
        )
        qs_params = self.alipay_api_instance.build_request(
            'alipay.user.info.share')
        qs_params.update(**biz_content)
        self.alipay_api_instance.sign_request(qs_params)
        try:
            resp = requests.post('{}?{}'.format(
                self.alipay_api_instance.API_GATEWAY,
                urlencode(qs_params)
            ))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ApiRequestError(e)

        resp_json = resp.json()
        user_info = resp_json.get('alipay_user_info_share_response', {})
        return user_info
