# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
import uuid

from django.core.cache import cache
from rest_framework.test import APITestCase

import config
from test.auto_test.steps.merchant import CashierManagerStep
from test.unittest.fake_factory.fake_factory import PayunionFactory, fake

logger = logging.getLogger(__name__)


class TestMerchantCashier(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.fake_factory = PayunionFactory()
        cls.merchant = cls.fake_factory.create_merchant(status=config.MERCHANT_STATUS.USING)
        cls.merchant_admin = cls.fake_factory.create_merchant_admin(
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant)

        cls.merchant_token = str(uuid.uuid4())
        user = dict(
            openid=cls.merchant_admin.wechat_openid,
            unionid=cls.merchant_admin.wechat_unionid,
            session_key=str(uuid.uuid4()),
        )
        # 创建或刷新token过期时间
        cache.set(cls.merchant_token, user, None)

    def test_add(self):
        cashier_info = dict(
            openid='fgddffdf',
            nickname=fake.name(),
            sex=1,
            province=fake.province(),
            city=fake.city_suffix(),
            country=fake.country(),
            headimgurl=fake.image_url(),
            privilege=["PRIVILEGE1", "PRIVILEGE2"],
            unionid=fake.md5(),
        )
        cashier_manager = CashierManagerStep(self)
        resp = cashier_manager.add_cashier(merchant_token=self.merchant_token,
                                           cashier_info=cashier_info)
        logger.info('merchant_add_cashier_resp:' + repr(resp['merchant_add_cashier_resp'].json()))
        new_cashier_id = resp['merchant_add_cashier_resp'].json()['id']
        self.assertEqual(len(resp['merchant_add_cashier_resp'].json()), 5)

        resp = cashier_manager.get_all_cashiers(merchant_token=self.merchant_token, )
        logger.info('get_all_cashiers resp:' + repr(resp.json()))
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(len(resp.json()[0]), 5)

        resp = cashier_manager.remove_cashier(merchant_token=self.merchant_token,
                                              cashier_id=new_cashier_id)
        logger.info('remove_cashier resp:' + repr(resp.json()))
        self.assertEqual(len(resp.json()), 0)

        resp = cashier_manager.get_all_cashiers(merchant_token=self.merchant_token, )
        logger.info('get_all_cashiers resp:' + repr(resp.json()))
        self.assertEqual(len(resp.json()), 0)

        resp = cashier_manager.remove_cashier(merchant_token=self.merchant_token,
                                              cashier_id=new_cashier_id)
        logger.info('remove_cashier resp:' + repr(resp.json()))
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(resp.json()['error_code'], 'cashier does not exist')
