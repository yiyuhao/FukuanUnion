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
    def setUp(self):
        self.factory = PayunionFactory()

        try:
            self.platform_account = Account.objects.get(id=1)
        except Account.DoesNotExist:
            self.platform_account = self.factory.create_account(id=1, balance=0,
                                                                withdrawable_balance=0,
                                                                alipay_balance=0,
                                                                alipay_withdrawable_balance=0)
        self.originator_account = self.factory.create_account(real_name='引流商户', balance=0,
                                                              withdrawable_balance=0,
                                                              alipay_balance=0,
                                                              alipay_withdrawable_balance=0)
        self.merchant_account = self.factory.create_account(real_name='收款', balance=0,
                                                            withdrawable_balance=0,
                                                            alipay_balance=0,
                                                            alipay_withdrawable_balance=0)
        self.inviter_account = self.factory.create_account(real_name='邀请人', balance=0,
                                                           withdrawable_balance=0,
                                                           alipay_balance=0,
                                                           alipay_withdrawable_balance=0)
        self.inviter = self.factory.create_marketer(account=self.inviter_account)

        self.test_client = self.factory.create_client(openid='oUkVN5ZFKfLOkAFwkk4oGYVc0rfg',
                                                      status=0)
        self.merchant = self.factory.create_merchant(account=self.merchant_account,
                                                     status=1,
                                                     inviter=self.inviter)
        self.originator = self.factory.create_merchant(account=self.originator_account)
        self.rule = self.factory.create_coupon_rule(merchant=self.merchant)
        self.coupon = self.factory.create_coupon(rule=self.rule, client=self.test_client,
                                                 originator_merchant=self.originator,
                                                 min_charge=1000, discount=100,
                                                 status=COUPON_STATUS['NOT_USED'])

        self.merchant_admin = self.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,
            work_merchant=self.merchant
        )
        super(GetMerchantInfoTestCase, self).setUp()

    def test_payment_entry(self):
        url = reverse('payment_entry')
        response = self.client.get(url + '?uuid=bb0add6a-f424-4cb7-862e-fcd98d6447e7')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://openauth.alipaydev.com/oauth2/publicAppAuthorize.htm?app_id=2016091800543597&scope=auth_base&redirect_uri=http%3A//payweb.alpha.muchbo.com/pay.html&state=bb0add6a-f424-4cb7-862e-fcd98d6447e7')

    def test_get_merchant_info(self):
        url = reverse('payment-merchant-info')
        response = self.client.get(url, data={'uuid': self.merchant.payment_qr_code.uuid},
                                   format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {
            'id': self.merchant.id,
            'name': self.merchant.name,
            'description': self.merchant.description,
            'avatar_url': self.merchant.avatar_url,
            'status': self.merchant.status,
        })

    def test_place_order_with_coupon(self):
        url = reverse('place_order')
        response = self.client.post(
            url,
            data=dict(
                merchant_id=self.merchant.id,
                order_price=1000,
                channel=0,
                coupon_id=self.coupon.id,
            ),
            format='json')
        resp_json = response.json()
        assert len(resp_json['payment_serial_number']) == 32
        assert len(resp_json['client_payment_params']) == 6
        assert len(resp_json['client_payment_params']['appId']) == 18
        assert len(resp_json['client_payment_params']['timeStamp']) == 10
        assert len(resp_json['client_payment_params']['nonceStr']) == 32
        assert len(resp_json['client_payment_params']['package']) == 46
        assert resp_json['client_payment_params']['signType'] == 'MD5'
        assert len(resp_json['client_payment_params']['paySign']) == 32
        return resp_json

    def test_place_order_without_coupon(self):
        url = reverse('place_order')
        response = self.client.post(
            url,
            data=dict(
                merchant_id=self.merchant.id,
                order_price=1000,
                channel=0,
                coupon_id=None,
            ),
            format='json')
        resp_json = response.json()
        assert len(resp_json['payment_serial_number']) == 32
        assert len(resp_json['client_payment_params']) == 6
        assert len(resp_json['client_payment_params']['appId']) == 18
        assert len(resp_json['client_payment_params']['timeStamp']) == 10
        assert len(resp_json['client_payment_params']['nonceStr']) == 32
        assert len(resp_json['client_payment_params']['package']) == 46
        assert resp_json['client_payment_params']['signType'] == 'MD5'
        assert len(resp_json['client_payment_params']['paySign']) == 32
        return resp_json
