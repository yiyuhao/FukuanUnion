#      File: test_merchant_admin_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/25
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from common.models import MerchantAdmin
from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES
from test.unittest.fake_factory import PayunionFactory
from common.model_manager.merchant_admin_manager import MerchantAdminModelManager, MerchantAdminManager


class TestMerchantAdminModelManager(TestCase):

    def setUp(self):
        self.factory = PayunionFactory()
        self.merchant = self.factory.create_merchant()
        self.merchant_admin = self.factory.create_merchant_admin(work_merchant=self.merchant)
        self.manager = MerchantAdminModelManager()

    def test_has_openid(self):
        # create multiple merchant
        for _ in range(10):
            self.factory.create_merchant()

        self.assertEqual(self.manager.get_merchant_admin(self.merchant_admin.wechat_unionid), self.merchant_admin)

        old_unionid = self.merchant_admin.wechat_unionid
        self.merchant_admin.wechat_unionid = 'another openid'
        self.merchant_admin.save()
        self.assertIsNone(self.manager.get_merchant_admin(old_unionid))

    def test_remove_cashier(self):
        cashier = self.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=self.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )
        self.manager.remove_cashier(cashier)
        cashier = MerchantAdmin.objects.get(id=cashier.id)
        self.assertEqual(cashier.status, SYSTEM_USER_STATUS['DISABLED'])


class TestMerchantAdminManager(TestCase):

    def setUp(self):
        self.factory = PayunionFactory()
        self.merchant = self.factory.create_merchant()
        self.merchant_admin = self.factory.create_merchant_admin(
            work_merchant=self.merchant,
            alipay_user_name='周杰偷'
        )
        self.manager = MerchantAdminManager(self.merchant_admin)

    def test_work_merchant(self):
        merchant = self.manager.work_merchant.obj
        self.assertEqual(merchant, self.merchant)

    def test_insensitive_alipay_user_name(self):
        self.assertEqual(self.manager.insensitive_alipay_user_name, '**偷')
