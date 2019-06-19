#      File: manually_test_login.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/21
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.core.cache import cache
from django.test import TestCase

from common.auth.wechat.login import MerchantLoginHandler, LoginError
from common.error_handler import MerchantError
from config import SYSTEM_USER_STATUS
from test.test_config import ManuallyTestMinaConfig as Config
from test.unittest.fake_factory import PayunionFactory


class TestMerchantAdminLogin(TestCase):

    def setUp(self):
        factory = PayunionFactory()
        self.merchant_admin = factory.create_merchant_admin(
            wechat_openid=Config.my_account_openid,
            status=SYSTEM_USER_STATUS['USING']
        )

    def test_login_success(self):
        login_handler = MerchantLoginHandler()
        token = login_handler.login(Config.wechat_login_code)
        self.assertIsNotNone(token, '返回token')
        cached_token = cache.get(token)  # (dict)
        self.assertIsNotNone(cached_token, 'redis缓存token')
        self.assertIn('openid', cached_token)
        self.assertIn('session_key', cached_token)

    def test_login_code_error(self):
        code = 'wrong wechat login code'

        login_handler = MerchantLoginHandler()
        with self.assertRaisesMessage(LoginError, MerchantError.get_openid_error['code']):
            _ = login_handler.login(code)

    def test_merchant_admin_not_exist_error(self):
        self.merchant_admin.wechat_openid = 'wrong open id'
        self.merchant_admin.save()

        login_handler = MerchantLoginHandler()
        with self.assertRaisesMessage(LoginError, MerchantError.user_is_not_a_merchant_admin['code']):
            _ = login_handler.login(Config.wechat_login_code)
