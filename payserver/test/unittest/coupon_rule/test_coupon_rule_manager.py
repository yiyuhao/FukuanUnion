#      File: test_coupon_rule_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/5
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import re

from django.test import TestCase
from django.utils import timezone

from common.model_manager.coupon_rule_manager import CouponRuleManager
from common.model_manager.utils import get_amount, set_amount
from config import COUPON_STATUS
from test.unittest.fake_factory import PayunionFactory


class Config:
    day_1 = timezone.datetime(year=2018, month=1, day=1)
    day_2 = timezone.datetime(year=2018, month=2, day=1)
    day_3 = timezone.datetime(year=2018, month=3, day=1)
    day_4 = timezone.datetime(year=2018, month=4, day=1)


class TestCouponRuleManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.coupon_rule = cls.factory.create_coupon_rule(discount=set_amount(100.1), min_charge=set_amount(300))
        cls.manager = CouponRuleManager(cls.coupon_rule)

    def test_detail(self):
        # 创建已领取的优惠券
        self.factory.create_coupon(number=8, rule=self.coupon_rule, status=COUPON_STATUS['NOT_USED'])
        self.factory.create_coupon(number=2, rule=self.coupon_rule, status=COUPON_STATUS['USED'])
        detail = self.manager.detail()
        self.assertEqual(detail, dict(
            merchant=self.coupon_rule.merchant.name,
            merchant_location_lon=self.coupon_rule.merchant.location_lon,
            merchant_location_lat=self.coupon_rule.merchant.location_lat,
            discount=get_amount(self.coupon_rule.discount),
            min_charge=get_amount(self.coupon_rule.min_charge),
            valid_strategy=self.coupon_rule.valid_strategy,
            start_date=self.coupon_rule.start_date,
            end_date=self.coupon_rule.end_date,
            expiration_days=self.coupon_rule.expiration_days,
            stock=self.coupon_rule.stock,
            photo_url=self.coupon_rule.photo_url,
            datetime=self.coupon_rule.datetime.date(),
            obtain_num=10,
            used_num=2
        ))

    def test_serialize_relative_payment(self):
        for day in (Config.day_1, Config.day_2, Config.day_3, Config.day_4):
            payment = self.factory.create_payment(
                coupon=self.factory.create_coupon(rule=self.coupon_rule),
                order_price=set_amount(300),
                datetime=day)
            self.factory.create_transaction(
                content_object=payment,
                amount=payment.order_price - self.coupon_rule.discount)
        payments = self.manager.relative_payment()[:20]  # page
        data = self.manager.serialize_relative_payment(payments)

        for e in data:
            day = e['month']
            payments = e['cur_page_transactions']
            self.assertTrue(re.match('2018-0[1-4]-01', day))
            self.assertIn(payments[0]['title'], ('微信支付', '支付宝支付'))
            self.assertEqual(payments[0]['desc'], '[满300减100.1优惠券]')
            self.assertTrue(re.match('0[1-4]-01 00:00', payments[0]['datetime']))
            self.assertEqual(payments[0]['amount'], 300 - 100.1)
            self.assertIn(payments[0]['status'], ('', '已退款', '退款中'))
