# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.test import TestCase

import config
from common.payment.base import PaymentBaseUseCases
from test.unittest.fake_factory import PayunionFactory


class PaymentBaseTestCases(TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.factory = PayunionFactory()

    def setUp(self):
        self.merchants = []
        self.merchants.append(self.factory.create_merchant(
            location_lon=39.913811,
            location_lat=116.410189,
            name='王府井百货',
            status=config.MERCHANT_STATUS.USING,
        ))

        self.merchants.append(self.factory.create_merchant(
            location_lon=39.909631,
            location_lat=116.423407,
            name='好苑建国饭店',
            status=config.MERCHANT_STATUS.USING,
        ))

        self.merchants.append(self.factory.create_merchant(
            location_lon=39.908775,
            location_lat=116.409802,
            name='北京饭店',
            status=config.MERCHANT_STATUS.USING,
        ))

        self.merchants.append(self.factory.create_merchant(
            location_lon=39.906668,
            location_lat=116.426454,
            name='湖南大厦',
            status=config.MERCHANT_STATUS.USING,
        ))

        self.merchants.append(self.factory.create_merchant(
            location_lon=39.960701,
            location_lat=116.323457,
            name='天作国际',
            status=config.MERCHANT_STATUS.USING,
        ))

        self.merchants.append(self.factory.create_merchant(
            location_lon=39.970503,
            location_lat=116.321054,
            name='当代商城',
            status=config.MERCHANT_STATUS.USING,
        ))

        for m in self.merchants:
            self.factory.create_coupon_rule(
                merchant=m,
                stock=100
            )

        self.payment = self.factory.create_payment(
            status=config.PAYMENT_STATUS.FROZEN,
            coupon_granted=False
        )

    def test_grant_coupons(self):
        coupons = PaymentBaseUseCases.grant_coupons(self.payment, 39.913384, 116.414437, 10)

        assert len(coupons) == 3
        valid_ids = {m.id for m in self.merchants[:4]}
        actual_ids = {c.rule.merchant.id for c in coupons}

        assert actual_ids < valid_ids

    def test_grant_coupons1(self):
        coupons = PaymentBaseUseCases.grant_coupons(self.payment, 39.962215, 116.32899310, 10)

        assert len(coupons) == 2
        valid_ids = {m.id for m in self.merchants[4:]}
        actual_ids = {c.rule.merchant.id for c in coupons}

        assert actual_ids <= valid_ids
