#
#      File: test_1.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid

from faker import Faker
from rest_framework.test import APITestCase

from common.model_manager.utils import set_amount
from config import MERCHANT_STATUS, MERCHANT_ADMIN_TYPES
from test.auto_test.steps.merchant import MerchantLoginMockStep, MerchantStep
from test.unittest.fake_factory import PayunionFactory

fake = Faker('zh_CN')


class TestMerchantViewSet(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

        # 商户分类
        cls.merchant_category = None
        for p in range(4):
            parent = cls.factory.create_merchant_category(name='parent{}'.format(p))
            for c in range(4):
                cls.merchant_category = cls.factory.create_merchant_category(
                    parent=parent,
                    name='{}_child{}'.format(parent.name, c))

        # 商户街道
        for p in range(4):
            parent = cls.factory.create_area(name='市{}'.format(p))
            for c in range(4):
                child = cls.factory.create_area(parent=parent, name='{}_区{}'.format(parent.name, c))
                for cc in range(4):
                    cls.area = cls.factory.create_area(parent=child,
                                                       name='{}_区{}_街道{}'.format(parent.name, c,
                                                                                 cc))

        cls.account = cls.factory.create_account(
            balance=set_amount(1000.00),
            withdrawable_balance=set_amount('500.05'),
            alipay_balance=set_amount(2000),
            alipay_withdrawable_balance=set_amount('1000.05'),
            bank_card_number='1234567890123',
        )

        cls.merchant = cls.factory.create_merchant(
            name='就是这个公司',
            status=MERCHANT_STATUS['USING'],
            account=cls.account,
            area=cls.area,
            category=cls.merchant_category,
            avatar_url='https://merchant_avatar.jpg',
            photo_url='https://merchant_photo.jpg',
            id_card_back_url=True,
            id_card_front_url=True,
            day_begin_minute=8 * 60,  # 商户订单日结时间设置为08:00
        )
        cls.merchant_admin = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN'],
            work_merchant=cls.merchant,
            alipay_user_name='张付宝'
        )
        cls.merchant_cashier = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            work_merchant=cls.merchant
        )

    def test_steps(self):
        # login
        resp = MerchantLoginMockStep(self).login(code=uuid.uuid4().hex,
                                                 mocked_openid=self.merchant_admin.wechat_openid,
                                                 mocked_unionid=self.merchant_admin.wechat_unionid)
        token = resp.json()['token']

        # get merchant info
        me = MerchantStep(self, token=token).me().json()
        self.assertEqual(me['name'], self.merchant.name)
