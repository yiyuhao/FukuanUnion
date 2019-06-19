#      File: test_coupon_rule_view_set.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/4
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import copy
import re

from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.error_handler import MerchantError
from common.model_manager.utils import set_amount, get_amount
from common.models import CouponRule
from config import VALID_STRATEGY, COUPON_STATUS, MERCHANT_STATUS, PAYMENT_STATUS
from test.api_test.merchant.utils import MerchantLoginedMixin
from test.unittest.fake_factory import PayunionFactory
from test.utils import NonFieldError
from test.utils import render


class Config:
    jan = timezone.datetime(year=2018, month=1, day=1)
    feb = timezone.datetime(year=2018, month=2, day=1)
    mar = timezone.datetime(year=2018, month=3, day=1)
    apr = timezone.datetime(year=2018, month=4, day=1)
    may = timezone.datetime(year=2018, month=5, day=1)
    day_1 = jan
    day_2 = feb
    day_3 = mar
    day_4 = apr

    @classmethod
    def strftime(cls, date):
        """date --> '2018-01-01'"""
        return date.strftime('%Y-%m-%d')


class TestCouponViewSet(MerchantLoginedMixin, APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.merchant = cls.factory.create_merchant(status=MERCHANT_STATUS['USING'])
        cls.merchant_admin = cls.factory.create_merchant_admin(work_merchant=cls.merchant)

        # 创建token并缓存, 绕过登录
        super(TestCouponViewSet, cls).setUpTestData()

    def _create_different_type_coupon_rules(self):
        # 指定日期区间
        self.factory.create_coupon_rule(
            merchant=self.merchant,
            discount=set_amount(100),
            min_charge=set_amount(300),
            valid_strategy=VALID_STRATEGY['DATE_RANGE'],
            start_date=Config.jan,
            end_date=Config.feb,
        )

        # 指定有效天数
        self.factory.create_coupon_rule(
            number=10,
            merchant=self.merchant,
            discount=set_amount(1000),
            min_charge=set_amount(3000),
            valid_strategy=VALID_STRATEGY['EXPIRATION'],
            expiration_days=90,
        )

    def _create_coupon_rule(self):
        self.coupon_rule = self.factory.create_coupon_rule(
            merchant=self.merchant,
            discount=set_amount(100.1),
            min_charge=set_amount(300),
        )
        for day in (Config.day_1, Config.day_2, Config.day_3, Config.day_4):
            for i in range(20):
                coupon = self.factory.create_coupon(
                    rule=self.coupon_rule,
                    status=(COUPON_STATUS['NOT_USED'], COUPON_STATUS['USED'])[i % 2])
                payment = self.factory.create_payment(
                    order_price=set_amount(300),
                    coupon=coupon,
                    status=PAYMENT_STATUS['FINISHED'],
                    datetime=day)
                self.factory.create_transaction(
                    content_object=payment,
                    amount=payment.order_price - self.coupon_rule.discount)

    def test_list(self):
        self._create_different_type_coupon_rules()
        url = reverse('coupon-list')
        response = self.client.get(url, Token=self.token)  # auth by token
        resp_json = response.json()
        self.assertEqual(len(resp_json), 11)
        for coupon_rule in resp_json:
            if coupon_rule['valid_strategy'] == VALID_STRATEGY['DATE_RANGE']:
                self.assertEqual(coupon_rule['start_date'], Config.strftime(Config.jan))
                self.assertEqual(coupon_rule['end_date'], Config.strftime(Config.feb))
                self.assertEqual(coupon_rule['discount'], 100)
                self.assertEqual(coupon_rule['min_charge'], 300)
            else:
                self.assertEqual(coupon_rule['discount'], 1000)
                self.assertEqual(coupon_rule['min_charge'], 3000)
                self.assertEqual(coupon_rule['expiration_days'], 90)

    def test_detail(self):
        self._create_coupon_rule()
        url = reverse('coupon-detail', kwargs=dict(pk=self.coupon_rule.id))
        response = self.client.get(url, Token=self.token)  # auth by token
        detail = response.json()

        self.assertEqual(detail, dict(
            merchant=self.merchant.name,
            merchant_location_lon=self.merchant.location_lon,
            merchant_location_lat=self.merchant.location_lat,
            discount=render(self.coupon_rule.discount),
            min_charge=render(self.coupon_rule.min_charge),
            valid_strategy=self.coupon_rule.valid_strategy,
            start_date=self.coupon_rule.start_date.strftime('%Y-%m-%d'),
            end_date=self.coupon_rule.end_date.strftime('%Y-%m-%d'),
            expiration_days=self.coupon_rule.expiration_days,
            stock=self.coupon_rule.stock,
            photo_url=self.coupon_rule.photo_url,
            datetime=self.coupon_rule.datetime.strftime('%Y-%m-%d'),
            obtain_num=80,
            used_num=40
        ))

        # 不存在的优惠券
        url = reverse('coupon-detail', kwargs=dict(pk='id_not_exist'))
        response = self.client.get(url, Token=self.token)  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

        # 非商户创建的优惠券
        another_coupon_rule = self.factory.create_coupon_rule()
        url = reverse('coupon-detail', kwargs=dict(pk=another_coupon_rule.id))
        response = self.client.get(url, Token=self.token)  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

    def test_create(self):

        # 指定日期范围
        url = reverse('coupon-list')
        coupon_rule_json = dict(
            discount=100,
            min_charge='300',
            valid_strategy=VALID_STRATEGY['DATE_RANGE'],
            start_date='2018-01-01',
            end_date='2018-01-01',
            stock=100,
            photo_url='a url',
            note='a note'
        )
        response = self.client.post(url, data=coupon_rule_json, Token=self.token,
                                    format='json')  # auth by token
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resp_json = response.json()

        # 检查response
        expect = copy.copy(coupon_rule_json)
        expect.update(dict(
            discount=coupon_rule_json['discount'],
            min_charge=int(coupon_rule_json['min_charge']),
            expiration_days=None,
        ))
        self.assertEqual(resp_json, expect)

        # 检查创建的coupon_rule
        coupon_rule = CouponRule.objects.filter(
            merchant=self.merchant, stock=coupon_rule_json['stock']
        ).first()
        self.assertEqual(coupon_rule.discount, set_amount(coupon_rule_json['discount']))
        self.assertEqual(coupon_rule.min_charge, set_amount(coupon_rule_json['min_charge']))
        self.assertEqual(coupon_rule.valid_strategy, coupon_rule_json['valid_strategy'])
        self.assertEqual(str(coupon_rule.start_date), coupon_rule_json['start_date'])
        self.assertEqual(str(coupon_rule.end_date), coupon_rule_json['end_date'])
        self.assertEqual(coupon_rule.expiration_days, None)
        self.assertEqual(coupon_rule.stock, coupon_rule_json['stock'])
        self.assertEqual(coupon_rule.photo_url, coupon_rule_json['photo_url'])
        self.assertEqual(coupon_rule.note, coupon_rule_json['note'])

        # 参数格式不正确  减免金额小于最低消费
        data = copy.copy(coupon_rule_json)
        data.update(dict(
            discount=101,
            min_charge=100,
        ))
        response = self.client.post(url, data=data, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json,
                         NonFieldError(MerchantError.min_charge_must_greater_than_discount))

        # 参数格式不正确  无start_date 或 end_date
        data = copy.copy(coupon_rule_json)
        del data['start_date']
        response = self.client.post(url, data=data, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json,
                         NonFieldError(MerchantError.must_have_param_start_date_and_end_date))

        # 参数格式不正确  需 start_date <= end_date
        data = copy.copy(coupon_rule_json)
        data.update(dict(
            start_date='2018-03-01',
            end_date='2018-01-01',
        ))
        response = self.client.post(url, data=data, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json,
                         NonFieldError(MerchantError.end_date_must_greater_than_start_date))

        # 指定有效天数
        coupon_rule_json = dict(
            discount=100,
            min_charge='300',
            valid_strategy=VALID_STRATEGY['EXPIRATION'],
            expiration_days=90,
            stock=200,
            photo_url='another url',
            note='another note'
        )
        response = self.client.post(url, data=coupon_rule_json, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()

        # 检查response
        expect = copy.copy(coupon_rule_json)
        expect.update(dict(
            discount=coupon_rule_json['discount'],
            min_charge=float(coupon_rule_json['min_charge']),
            start_date=None,
            end_date=None,
        ))
        self.assertEqual(resp_json, expect)

        # 检查创建的coupon_rule
        coupon_rule = CouponRule.objects.filter(
            merchant=self.merchant, stock=coupon_rule_json['stock']
        ).first()
        self.assertEqual(coupon_rule.valid_strategy, coupon_rule_json['valid_strategy'])
        self.assertEqual(coupon_rule.start_date, None)
        self.assertEqual(coupon_rule.end_date, None)
        self.assertEqual(coupon_rule.expiration_days, coupon_rule_json['expiration_days'])

        # 参数格式不正确  指定有效天数时无expiration_days
        data = copy.copy(coupon_rule_json)
        del data['expiration_days']
        response = self.client.post(url, data=data, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MerchantError.must_have_param_expiration_days))

        # 有效天数不正确需>0
        data = copy.copy(coupon_rule_json)
        data['expiration_days'] = 0
        response = self.client.post(url, data=data, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json,
                         {'expiration_days': ['请确保该值大于或者等于 1。'], 'error_code': 'min_value'})

        # 参数格式不正确 满减金额与最低消费必须为整数
        # 指定有效天数
        coupon_rule_json = dict(
            discount=100,
            min_charge='300.01',
            valid_strategy=VALID_STRATEGY['EXPIRATION'],
            expiration_days=90,
            stock=200,
            photo_url='another url',
            note='another note'
        )
        response = self.client.post(url, data=coupon_rule_json, Token=self.token,
                                    format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json,
                         {'min_charge': ['请确保总计不超过 0 个小数位。'], 'error_code': 'max_decimal_places'})

    def test_update(self):
        self._create_coupon_rule()
        # 修改优惠券库存
        for stock in (0, 1, 300, 301):
            coupon_rule = self.coupon_rule
            old_update_datetime = coupon_rule.update_datetime

            url = reverse('coupon-detail', kwargs=dict(pk=self.coupon_rule.id))
            response = self.client.put(url, data=dict(stock=stock), Token=self.token,
                                       format='json')  # auth by token
            detail = response.json()
            self.assertEqual(detail, dict(
                discount=get_amount(self.coupon_rule.discount),
                min_charge=get_amount(self.coupon_rule.min_charge),
                valid_strategy=self.coupon_rule.valid_strategy,
                start_date=self.coupon_rule.start_date.strftime('%Y-%m-%d'),
                end_date=self.coupon_rule.end_date.strftime('%Y-%m-%d'),
                expiration_days=self.coupon_rule.expiration_days,
                stock=stock,
                photo_url=self.coupon_rule.photo_url,
                note=self.coupon_rule.note,
            ))

            # 检查修改库存的coupon_rule
            coupon_rule.refresh_from_db()

            self.assertEqual(coupon_rule.discount, set_amount(detail['discount']))
            self.assertEqual(coupon_rule.min_charge, set_amount(detail['min_charge']))
            self.assertEqual(coupon_rule.valid_strategy, detail['valid_strategy'])
            self.assertEqual(str(coupon_rule.start_date), detail['start_date'])
            self.assertEqual(str(coupon_rule.end_date), detail['end_date'])
            self.assertNotEqual(coupon_rule.update_datetime, old_update_datetime)

        # 不存在的优惠券
        url = reverse('coupon-detail', kwargs=dict(pk='id_not_exist'))
        response = self.client.put(url, Token=self.token, format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

        # 非商户创建的优惠券
        another_coupon_rule = self.factory.create_coupon_rule()
        url = reverse('coupon-detail', kwargs=dict(pk=another_coupon_rule.id))
        response = self.client.put(url, Token=self.token, format='json')  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

    def test_payments(self):
        self._create_coupon_rule()

        # 第一页
        url = reverse('coupon-payments', kwargs=dict(pk=self.coupon_rule.id))
        response = self.client.get(url, Token=self.token)  # auth by token
        data = response.json()['results']
        for e in data:
            day = e['month']
            payments = e['cur_page_transactions']
            self.assertTrue(re.match('2018-04-01', day))  # 按照时间排列
            self.assertIn(payments[0]['title'], ('微信支付', '支付宝支付'))
            self.assertEqual(payments[0]['desc'], '[满300减100.1优惠券]')
            self.assertEqual('04-01 00:00', payments[0]['datetime'])
            self.assertEqual(payments[0]['amount'], 300 - 100.1)
            self.assertIn(payments[0]['status'], ('', '已退款', '退款中'))
            self.assertIn('id', payments[0])

        # 第四页
        url = reverse('coupon-payments', kwargs=dict(pk=self.coupon_rule.id))
        response = self.client.get(url, dict(page=4), Token=self.token)  # auth by token
        data = response.json()['results']
        for e in data:
            day = e['month']
            payments = e['cur_page_transactions']
            self.assertTrue(re.match('2018-01-01', day))  # 按照时间排列
            self.assertIn(payments[0]['title'], ('微信支付', '支付宝支付'))
            self.assertEqual(payments[0]['desc'], '[满300减100.1优惠券]')
            self.assertEqual('01-01 00:00', payments[0]['datetime'])
            self.assertEqual(payments[0]['amount'], 300 - 100.1)
            self.assertIn(payments[0]['status'], ('', '已退款', '退款中'))

        # 不存在的优惠券
        url = reverse('coupon-payments', kwargs=dict(pk='id_not_exist'))
        response = self.client.get(url, Token=self.token)  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

        # 非商户创建的优惠券
        another_coupon_rule = self.factory.create_coupon_rule()
        url = reverse('coupon-payments', kwargs=dict(pk=another_coupon_rule.id))
        response = self.client.get(url, Token=self.token)  # auth by token
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})
