# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.models import Account
from config import MERCHANT_ADMIN_TYPES, COUPON_STATUS
from test.api_test.puser.utils import ClientLoggedInMixin
from test.unittest.fake_factory import PayunionFactory


class GetMerchantInfoTestCase(ClientLoggedInMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

        try:
            cls.platform_account = Account.objects.get(id=1)
        except Account.DoesNotExist:
            cls.platform_account = cls.factory.create_account(id=1, balance=0,
                                                              withdrawable_balance=0,
                                                              alipay_balance=0,
                                                              alipay_withdrawable_balance=0)
        cls.originator_account = cls.factory.create_account(real_name='引流商户', balance=0,
                                                            withdrawable_balance=0,
                                                            alipay_balance=0,
                                                            alipay_withdrawable_balance=0)
        cls.merchant_account = cls.factory.create_account(real_name='收款', balance=0,
                                                          withdrawable_balance=0,
                                                          alipay_balance=0,
                                                          alipay_withdrawable_balance=0)
        cls.inviter_account = cls.factory.create_account(real_name='邀请人', balance=0,
                                                         withdrawable_balance=0,
                                                         alipay_balance=0,
                                                         alipay_withdrawable_balance=0)
        cls.inviter = cls.factory.create_marketer(account=cls.inviter_account)

        cls.test_client = cls.factory.create_client(openid='1234567890', status=0)
        cls.merchant = cls.factory.create_merchant(account=cls.merchant_account,
                                                   inviter=cls.inviter)
        cls.originator = cls.factory.create_merchant(account=cls.originator_account)
        cls.rule = cls.factory.create_coupon_rule(merchant=cls.merchant)
        cls.coupon = cls.factory.create_coupon(rule=cls.rule, client=cls.test_client,
                                               originator_merchant=cls.originator,
                                               min_charge=1000, discount=100,
                                               status=COUPON_STATUS['NOT_USED'])

        cls.merchant_admin = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,
            work_merchant=cls.merchant
        )
        super(GetMerchantInfoTestCase, cls).setUpTestData()

    def test_me(self):
        url = reverse('client-me')
        self.client.credentials(HTTP_ACCESS_TOKEN=self.token)
        response = self.client.get(url, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {
            'openid_channel': self.test_client.openid_channel,
            'status': self.test_client.status,
            'avatar_url': self.test_client.avatar_url,
            'phone_known': True
        })
