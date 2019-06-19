#
#      File: test_refund_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES
from common.model_manager.refund_manager import RefundManager
from test.test_config import ManuallyTestMinaConfig as Config
from test.unittest.fake_factory import PayunionFactory


class TestRefundManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.merchant = cls.factory.create_merchant()
        cls.merchant_admin = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN'],
            wechat_openid=Config.my_account_openid
        )
        cls.payment = cls.factory.create_payment(
            merchant=cls.merchant,
            order_price=300,
        )
        cls.refund = cls.factory.create_refund(
            serial_number='refund serial_number',
            payment=cls.payment,
        )
        cls.manager = RefundManager(cls.refund)

    def manually_test_refund_message(self):

        self.manager.send_refund_success_message()
        self.manager.send_refund_fail_message()
