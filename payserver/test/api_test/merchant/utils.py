#      File: utils.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/26
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import uuid

from django.core.cache import cache


class MerchantLoginedMixin:
    """
        must be first e.g.
        class TestStatistics(MerchantLoginedMixin, APITestCase):
    """

    @classmethod
    def setUpTestData(cls):

        if hasattr(cls, 'merchant_admin'):
            cls.token = uuid.uuid4()
            cache.set(cls.token, dict(
                openid=cls.merchant_admin.wechat_openid,
                unionid=cls.merchant_admin.wechat_unionid,
                session_key='session key'), 300)

        if hasattr(cls, 'merchant_cashier'):
            cls.cashier_token = uuid.uuid4()
            cache.set(cls.cashier_token, dict(
                openid=cls.merchant_cashier.wechat_openid,
                unionid=cls.merchant_cashier.wechat_unionid,
                session_key='cashier session key'), 300)
