# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

from common.auth.internal.validate_util import TokenGenerate
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase
from dynaconf import settings as dynasettings

REFRESH_TOKEN = dynasettings.INTERNAL_AUTH_TOKEN_CONFIG_REFRESH_TOKEN
CURRENT_ENV = dynasettings.ENV

class RefreshAccessTokenTests(AdminSystemTestBase):

    def test_refresh_token(self):
        """ 刷新公众号token """

        url = '/api/admin/wechat/access_token/refresh'

        invalid_params = TokenGenerate(REFRESH_TOKEN, 'refresh_token1').get_token_params()
        resp = self.client.post(url, data=invalid_params, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        user_valid_params = TokenGenerate(REFRESH_TOKEN, 'refresh_token').get_token_params()
        user_valid_params.update({'account_type': 'user'})
        resp = self.client.post(url, data=user_valid_params, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['detail'], 'refresh_ok')

    def test_obtain_token(self):

        url = '/api/admin/wechat/access_token/obtain'
        valid_params = TokenGenerate(REFRESH_TOKEN, 'refresh_token').get_token_params()
        resp = self.client.post(url, data=valid_params, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(len(resp_json), 3)
        self.assertIn('user', resp_json.keys())
        self.assertIn('merchant', resp_json.keys())
        self.assertIn('merchant', resp_json.keys())