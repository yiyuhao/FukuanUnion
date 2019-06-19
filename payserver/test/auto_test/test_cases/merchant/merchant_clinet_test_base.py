# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid

import config
from rest_framework.test import APITestCase
from test.auto_test.steps.merchant import MerchantLoginMockStep


class MerchantClientTestBase(APITestCase):
    def mock_merchant_admin_or_cashier_login_success(self, wechat_person_obj, is_chashier=False):
        login_step = MerchantLoginMockStep(self)
        resp = login_step.login(str(uuid.uuid4()),
                                mocked_openid=wechat_person_obj.mini_openid,
                                mocked_session_key=wechat_person_obj.mini_session_key,
                                mocked_unionid=wechat_person_obj.unionid,
                                )
        resp_json = resp.json()
        # 商户管理员或收银员登录成功
        if is_chashier:
            self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['CASHIER'])
        else:
            self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['ADMIN'])
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['USING'])
        return resp_json['token']