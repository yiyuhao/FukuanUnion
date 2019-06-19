# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import re

import requests_mock
from rest_framework.reverse import reverse

from test.auto_test.callback.alipay import AlipayCode2AccessTokenCallback
from test.auto_test.callback.wechat import WXCode2SessionCallback
from test.auto_test.steps.base import BaseStep


class ClientSteps(BaseStep):

    def wechat_login(self, code, mocked_openid=None, mocked_session_key=None, mocked_unionid=None,
                     validate=None):
        pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/jscode2session\?.+$')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', pattern,
                           json=WXCode2SessionCallback(code, mocked_openid,
                                                       mocked_session_key,
                                                       mocked_unionid,
                                                       validate=validate).mock_success)
            url = reverse('client-login')
            resp = self.client.post(url,
                                    data={'code': code, 'channel': 0},
                                    format='json')
            return resp.json()

    def alipay_login(self, code, mocked_user_id, validate):
        pattern = re.compile(r'^https://openapi\.alipaydev\.com/gateway\.do\?'
                             r'.*method=alipay\.system\.oauth\.token.*$')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern,
                           json=AlipayCode2AccessTokenCallback(code,
                                                               mocked_user_id,
                                                               validate=validate).mock_success)
            url = reverse('client-login')
            resp = self.client.post(url,
                                    data={'code': code, 'channel': 1},
                                    format='json')
            return resp.json()

    def me(self, access_token):
        url = reverse('client-me')
        self.client.credentials(HTTP_ACCESS_TOKEN=access_token)
        resp = self.client.get(url)
        self.client.credentials()
        return resp.json()

    def set_phone(self, access_token, iv, encrypted_data):
        url = reverse('client-set-phone')
        self.client.credentials(HTTP_ACCESS_TOKEN=access_token)
        resp = self.client.post(url, data={
            'iv': iv, 'encrypted_data': encrypted_data},
                                format='json')
        self.client.credentials()
        return resp.json()

    def get_coupons(self, access_token, uuid=None):
        url = reverse('client-coupon-list')
        self.client.credentials(HTTP_ACCESS_TOKEN=access_token)
        resp = self.client.get(url, data={'uuid': uuid} if uuid else {})
        self.client.credentials()
        return resp.json()

    def get_merchant_info(self, access_token, uuid):
        url = reverse('payment-merchant-info')
        self.client.credentials(HTTP_ACCESS_TOKEN=access_token)
        resp = self.client.get(url, data={'uuid': uuid})
        self.client.credentials()
        return resp.json()
