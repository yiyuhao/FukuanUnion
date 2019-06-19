# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

import config
from test.auto_test.steps.common_object import WechatPerson, fake
from test.auto_test.steps.merchant import CouponStep
from test.auto_test.test_cases.merchant.merchant_clinet_test_base import MerchantClientTestBase
from test.unittest.fake_factory import PayunionFactory


class TestCouponManage(MerchantClientTestBase):
    """ 商户端-卡券管理测试"""

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

        # 创建一个商铺及其管理员和收银员各一个
        cls.wechat_person_admin = WechatPerson()
        cls.wechat_person_cashier = WechatPerson()

        # 创建商户b 并设管理员, 收银员
        cls.merchatn_b = cls.factory.create_merchant(status=config.MERCHANT_STATUS['USING'])
        cls.factory.create_merchant_admin(
            wechat_openid=cls.wechat_person_admin.subscription_openid,
            wechat_unionid=cls.wechat_person_admin.unionid,
            wechat_avatar_url=cls.wechat_person_admin.user_info['headimgurl'],
            wechat_nickname=cls.wechat_person_admin.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchatn_b
        )
        cls.factory.create_merchant_admin(
            wechat_openid=cls.wechat_person_cashier.subscription_openid,
            wechat_unionid=cls.wechat_person_cashier.unionid,
            wechat_avatar_url=cls.wechat_person_cashier.user_info['headimgurl'],
            wechat_nickname=cls.wechat_person_cashier.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['CASHIER'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchatn_b
        )

    def test_create_coupon(self):
        """ 创建卡券 """

        wechat_person_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        admin_coupon_step = CouponStep(self, wechat_person_admin_token)

        wechat_person_cashier_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        cashier_coupon_step = CouponStep(self, wechat_person_cashier_token)

        # 金额验证
        coupon_data = dict(
            discount=100,
            min_charge=80,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-10-1',
            photo_url=fake.image_url()
        )
        resp = admin_coupon_step.create(**coupon_data)
        self.assertEqual(resp.json(),
                         {'non_field_errors': ['最低消费必须大于优惠金额'],
                          'error_code': 'min_charge must be greater than discount when valid_strategy is DATE_RANGE'
                          }
                         )
        resp = cashier_coupon_step.create(**coupon_data)
        self.assertEqual(resp.json(),
                         {'non_field_errors': ['最低消费必须大于优惠金额'],
                          'error_code': 'min_charge must be greater than discount when valid_strategy is DATE_RANGE'
                          }
                         )

        # 有效期验证（N天内有效）
        coupon_data = dict(
            discount=100,
            min_charge=180,
            valid_strategy=config.VALID_STRATEGY['EXPIRATION'],
            stock=10,
            expiration_days=0,
            photo_url=fake.image_url()
        )
        resp = admin_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)  # 有效期天数必须大于零
        self.assertEqual(resp.json(),
                         {'expiration_days': ['请确保该值大于或者等于 1。'], 'error_code': 'min_value'}
                         )
        resp = cashier_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.json(),
                         {'expiration_days': ['请确保该值大于或者等于 1。'], 'error_code': 'min_value'}
                         )

        # 有效期验证（时间段）
        coupon_data = dict(
            discount=100,
            min_charge=180,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2020-10-1',
            photo_url=fake.image_url()
        )
        resp = admin_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)  # 时间范围一年内
        self.assertEqual(resp.json(),
                         {'non_field_errors': ['结束时间必须在开始时间后一年内'],
                          'error_code': 'start date must be in 1 year from start date'}
                         )

        resp = cashier_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.json(),
                         {'non_field_errors': ['结束时间必须在开始时间后一年内'],
                          'error_code': 'start date must be in 1 year from start date'}
                         )

        # 卡券创建成功，库存图片验证与卡券投放
        # 管理员创建卡券，收银员查看卡券列表
        coupon_data = dict(
            discount=100,
            min_charge=180,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        resp = admin_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp_json = cashier_coupon_step.list().json()
        self.assertEqual(len(resp_json), 1)
        self.assertEqual(resp_json[0]['discount'], coupon_data['discount'])
        self.assertEqual(resp_json[0]['min_charge'], coupon_data['min_charge'])
        self.assertEqual(resp_json[0]['valid_strategy'], coupon_data['valid_strategy'])
        self.assertEqual(resp_json[0]['stock'], coupon_data['stock'])

        # 收银员创建卡券，管理员查看卡券列表
        coupon_data = dict(
            discount=5,
            min_charge=15,
            valid_strategy=config.VALID_STRATEGY['EXPIRATION'],
            stock=10,
            expiration_days=10,
            photo_url=fake.image_url()
        )
        resp = cashier_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp_json = admin_coupon_step.list().json()
        self.assertEqual(len(resp_json), 2)
        self.assertEqual(resp_json[0]['discount'], coupon_data['discount'])
        self.assertEqual(resp_json[0]['min_charge'], coupon_data['min_charge'])
        self.assertEqual(resp_json[0]['valid_strategy'], coupon_data['valid_strategy'])
        self.assertEqual(resp_json[0]['stock'], coupon_data['stock'])

    def test_coupon_list(self):
        """ 测试卡券列表 """
        # 创建卡券
        coupon_data1 = dict(
            discount=100,
            min_charge=180,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data2 = dict(
            discount=5,
            min_charge=15,
            valid_strategy=config.VALID_STRATEGY['EXPIRATION'],
            stock=10,
            expiration_days=10,
            photo_url=fake.image_url()
        )
        coupon_data3 = dict(
            discount=30,
            min_charge=60,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2017-10-1',
            end_date='2018-5-1',
            photo_url=fake.image_url()
        )
        coupon_data4 = dict(
            discount=20,
            min_charge=50,
            valid_strategy=config.VALID_STRATEGY['EXPIRATION'],
            stock=0,
            expiration_days=10,
            photo_url=fake.image_url()
        )
        wechat_person_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        admin_coupon_step = CouponStep(self, wechat_person_admin_token)

        wechat_person_cashier_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        cashier_coupon_step = CouponStep(self, wechat_person_cashier_token)

        resp = cashier_coupon_step.create(**coupon_data1)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = cashier_coupon_step.create(**coupon_data2)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = cashier_coupon_step.create(**coupon_data3)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = cashier_coupon_step.create(**coupon_data4)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = admin_coupon_step.list()
        resp_json = resp.json()
        self.assertEqual(len(resp_json), 4)

    def test_modify_stock(self):
        """ 修改卡券库存和下架卡券"""
        wechat_person_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        admin_coupon_step = CouponStep(self, wechat_person_admin_token)

        wechat_person_cashier_token = self.mock_merchant_admin_or_cashier_login_success(
            self.wechat_person_admin)
        cashier_coupon_step = CouponStep(self, wechat_person_cashier_token)
        coupon_data = dict(
            discount=100,
            min_charge=180,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        resp = cashier_coupon_step.create(**coupon_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp_json = cashier_coupon_step.list().json()
        self.assertEqual(resp_json[0]['stock'], coupon_data['stock'])
        coupon_rule_id = resp_json[0]['id']

        new_stock = 999
        resp = cashier_coupon_step.update(coupon_rule_id, new_stock)
        self.assertEqual(resp.json()['stock'], new_stock)

        new_stock = 0
        resp = admin_coupon_step.update(coupon_rule_id, new_stock)
        self.assertEqual(resp.json()['stock'], new_stock)
