# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid

from dynaconf import settings as dynasettings

import config
from common import models
from common.model_manager.payment_manager import alipay_payment
from common.models import Account, Area, MerchantAdmin
from test.auto_test.steps.alipay import AlipayPaymentSteps
from test.auto_test.steps.client import ClientSteps
from test.auto_test.steps.common_object import WechatPerson, fake
from test.auto_test.steps.inviter import GetUserInfoStep
from test.auto_test.steps.merchant import TransactionStep, CouponStep
from test.auto_test.steps.shared_pay import SharedPaySteps
from test.auto_test.steps.system_admin import LoginStep, FinancialQueryStep
from test.auto_test.test_cases.merchant.merchant_clinet_test_base import MerchantClientTestBase
from test.auto_test.workflows.pre_inviter import GenerateInviterWorkflow
from test.test_config import AutoTestConfig
from test.unittest.fake_factory import PayunionFactory
from test.unittest.system_admin.base_data import create_base_data


class TestUserPay(MerchantClientTestBase):

    def setUp(self):
        self.ALIPAY_PUBLIC_KEY_backup = dynasettings.ALIPAY_PUBLIC_KEY
        dynasettings.ALIPAY_PUBLIC_KEY = AutoTestConfig.self_generated_alipay_public_key
        alipay_payment.api_instance.alipay_public_key = AutoTestConfig.self_generated_alipay_public_key
        create_base_data()

        self.factory = PayunionFactory()
        try:
            self.platform_account = Account.objects.get(id=1)
        except Account.DoesNotExist:
            self.platform_account = self.factory.create_account(id=1, balance=0,
                                                                withdrawable_balance=0,
                                                                alipay_balance=0,
                                                                alipay_withdrawable_balance=0)

        #  三个商户信息
        # 创建三个商户ABC
        # |A-B = 4| < 5 && |B-C=4| < 5 && |A-C=8| > 5
        # A: 成都市武侯区锦城大道666号奥克斯广场F1  lng= 104.06147  lat= 30.57592  adcode = 510107062000
        # B: 成都市武侯区益州大道1999号银泰城F1  lng= 104.05847  lat= 30.54097  adcode = 510107062000
        # C: 成都市天府新区华阳街道正西街88号  lng= 104.05365  lat= 30.5062  adcode = 510116003000
        merchant_info_a = dict(
            address_info=dict(
                adcode='510107062000',
                address='成都市武侯区锦城大道666号奥克斯广场F1',
                location_lon=30.57592,
                location_lat=104.06147
            ),
            merchant_name='商户a',
            merchant_acct_data=dict(
                bank_name="工商银行",
                bank_card_number='622312131213122',
                real_name="商户a"
            )
        )
        merchant_info_b = dict(
            address_info=dict(
                adcode='510107062000',
                address='成都市武侯区益州大道1999号银泰城F1',
                location_lon=30.54097,
                location_lat=104.05847
            ),
            merchant_name='商户b',
            merchant_acct_data=dict(
                bank_name="工商银行",
                bank_card_number='622312131213123',
                real_name="商户b"
            )
        )
        merchant_info_c = dict(
            address_info=dict(
                adcode='510116003000',
                address='成都市天府新区华阳街道正西街88号',
                location_lon=30.5062,
                location_lat=104.05365
            ),
            merchant_name='商户c',
            merchant_acct_data=dict(
                bank_name="工商银行",
                bank_card_number='622312131213124',
                real_name="商户c"
            )
        )

        inviter_workflow = GenerateInviterWorkflow(self)

        new_work_ids_1 = [area.id for area in Area.objects.filter(parent__name='武侯区')]
        salesman_info_1 = dict(
            set_salesman=True,
            system_admin_name='admin@mishitu.com',
            system_admin_password='123456',
            new_work_ids=new_work_ids_1,
            worker_number='0001'
        )

        new_work_ids_2 = [area.id for area in Area.objects.filter(parent__name='武侯区')]
        salesman_info_2 = dict(
            set_salesman=True,
            system_admin_name='admin@mishitu.com',
            system_admin_password='123456',
            new_work_ids=new_work_ids_2,
            worker_number='0002'
        )

        new_work_ids_3 = [area.id for area in Area.objects.filter(parent__name='双流区')]
        salesman_info_3 = dict(
            set_salesman=True,
            system_admin_name='admin@mishitu.com',
            system_admin_password='123456',
            new_work_ids=new_work_ids_3,
            worker_number='0003'
        )

        # 成为邀请人且设为业务员
        res_info_1 = inviter_workflow.generate_inviter(name='邀请人1', salesman_info=salesman_info_1)
        res_info_2 = inviter_workflow.generate_inviter(name='邀请人2', salesman_info=salesman_info_2)
        res_info_3 = inviter_workflow.generate_inviter(name='邀请人3', salesman_info=salesman_info_3)

        res_data_1 = inviter_workflow.invite_merchant(inviter_token=res_info_1['token'],
                                                      merchant_info=merchant_info_a)
        res_data_2 = inviter_workflow.invite_merchant(inviter_token=res_info_2['token'],
                                                      merchant_info=merchant_info_b)
        res_data_3 = inviter_workflow.invite_merchant(inviter_token=res_info_3['token'],
                                                      merchant_info=merchant_info_c)

        # 业务员1，2, 3 分别审核a,b,c 通过
        aduit_a = inviter_workflow.aduit_merchant(config.MERCHANT_STATUS.USING,
                                                  token=res_info_1['token'],
                                                  merchant_id=res_data_1['merchant_id']
                                                  )
        aduit_b = inviter_workflow.aduit_merchant(config.MERCHANT_STATUS.USING,
                                                  token=res_info_2['token'],
                                                  merchant_id=res_data_2['merchant_id']
                                                  )
        aduit_c = inviter_workflow.aduit_merchant(config.MERCHANT_STATUS.USING,
                                                  token=res_info_3['token'],
                                                  merchant_id=res_data_3['merchant_id']
                                                  )

        res_info_1.update(dict(db_instance=models.Marketer.objects.get(pk=res_info_1['id'])))
        res_info_2.update(dict(db_instance=models.Marketer.objects.get(pk=res_info_2['id'])))
        res_info_3.update(dict(db_instance=models.Marketer.objects.get(pk=res_info_3['id'])))
        res_data_1.update(
            dict(db_instance=models.Merchant.objects.get(pk=res_data_1['merchant_id'])))
        res_data_2.update(
            dict(db_instance=models.Merchant.objects.get(pk=res_data_2['merchant_id'])))
        res_data_3.update(
            dict(db_instance=models.Merchant.objects.get(pk=res_data_3['merchant_id'])))

        self.inviter_info = {
            "a": res_info_1,
            "b": res_info_2,
            "c": res_info_3,
        }
        self.merchatn_info = {
            "a": res_data_1,
            "b": res_data_2,
            "c": res_data_3,
        }
        self.system_admin_info = {
            'username': 'admin@mishitu.com',
            'password': '123456'
        }

        # #  每个商户分别创建4种优惠券
        coupon_data_1 = dict(
            discount=5,
            min_charge=11,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_2 = dict(
            discount=8,
            min_charge=15,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_3 = dict(
            discount=12,
            min_charge=17,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_4 = dict(
            discount=15,
            min_charge=19,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        self.create_coupon_rule_data(res_data_1['merchant_id'], coupon_data_1)
        self.create_coupon_rule_data(res_data_1['merchant_id'], coupon_data_2)
        self.create_coupon_rule_data(res_data_1['merchant_id'], coupon_data_3)
        self.create_coupon_rule_data(res_data_1['merchant_id'], coupon_data_4)

        # b商户
        coupon_data_1 = dict(
            discount=10,
            min_charge=20,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=1,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_2 = dict(
            discount=10,
            min_charge=20,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=1,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_3 = dict(
            discount=20,
            min_charge=30,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=1,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_4 = dict(
            discount=20,
            min_charge=30,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=1,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        self.create_coupon_rule_data(res_data_2['merchant_id'], coupon_data_1)
        self.create_coupon_rule_data(res_data_2['merchant_id'], coupon_data_2)
        self.create_coupon_rule_data(res_data_2['merchant_id'], coupon_data_3)
        self.create_coupon_rule_data(res_data_2['merchant_id'], coupon_data_4)

        coupon_data_1 = dict(
            discount=45,
            min_charge=51,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_2 = dict(
            discount=48,
            min_charge=55,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_3 = dict(
            discount=52,
            min_charge=57,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        coupon_data_4 = dict(
            discount=55,
            min_charge=59,
            valid_strategy=config.VALID_STRATEGY['DATE_RANGE'],
            stock=10,
            start_date='2018-10-1',
            end_date='2019-5-1',
            photo_url=fake.image_url()
        )
        self.create_coupon_rule_data(res_data_3['merchant_id'], coupon_data_1)
        self.create_coupon_rule_data(res_data_3['merchant_id'], coupon_data_2)
        self.create_coupon_rule_data(res_data_3['merchant_id'], coupon_data_3)
        self.create_coupon_rule_data(res_data_3['merchant_id'], coupon_data_4)

        super(TestUserPay, self).setUpTestData()

    def tearDown(self):
        dynasettings.ALIPAY_PUBLIC_KEY = self.ALIPAY_PUBLIC_KEY_backup
        alipay_payment.api_instance.alipay_public_key = self.ALIPAY_PUBLIC_KEY_backup

    def create_coupon_rule_data(self, merchant_id, coupon_rule_data):
        """ 每个商户分别创建4种优惠券"""
        merchant_admin = MerchantAdmin.objects.filter(
            work_merchant_id=merchant_id,
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN
        ).first()

        # 商户管理员a创建4种卡券
        merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            WechatPerson(unionid=merchant_admin.wechat_unionid,
                         subscription_openid=merchant_admin.wechat_openid
                         ))

        admin_coupon_step = CouponStep(self, merchant_admin_token)
        resp = admin_coupon_step.create(**coupon_rule_data)

    def test_user_alipay_not_use_coupon(self):
        """
        不使用优惠券付款
        :return:
        """

        # 用户支付宝支付 向a商户0.01 元后退款"""
        # 用户不同意地理位置授权，支付成功，获取商户B的优惠券共3张

        # 支付宝授权
        alipay_clent_step = ClientSteps()
        alipay_person_userid = str(uuid.uuid4().hex)
        alipay_person = alipay_clent_step.alipay_login(str(uuid.uuid4().hex), alipay_person_userid,
                                                       None)
        alipay_person_access_token = alipay_person['access_token']

        # 给商户a支付0.01元给商户
        money = 1
        alipay_payment_step = AlipayPaymentSteps(alipay_person_access_token)
        place_order_resp_json = alipay_payment_step.place_order(
            self.merchatn_info['a']['merchant_id'], money, None)

        # 支付宝支付成功回调
        resp = alipay_payment_step.payment_callback(dynasettings.ALIPAY_APP_ID,
                                                    alipay_person_userid,
                                                    place_order_resp_json['out_trade_no'],
                                                    1)
        self.assertEqual(resp.content.decode(), '"OK"')

        # 获取优惠券 , 未报告位置，获取三张b的优惠券
        resp_json = SharedPaySteps(alipay_person['access_token']).poll_result(
            place_order_resp_json['out_trade_no'], None, None, None)
        payment_info = resp_json['payment']
        self.assertEqual(payment_info['serial_number'], place_order_resp_json['out_trade_no'])
        self.assertEqual(payment_info['status'], config.PAYMENT_STATUS['FROZEN'])
        self.assertEqual(payment_info['order_price'], money)
        coupons = resp_json['coupons']
        self.assertEqual(len(coupons), 3)
        for coupon in coupons:
            self.assertEqual('商户b', coupon['rule']['merchant']['name'])
            self.assertEqual('商户a', coupon['originator_merchant'])

        # 打开用户端查看三张优惠券
        resp_json = alipay_clent_step.get_coupons(alipay_person_access_token)
        self.assertEqual(resp_json, coupons)

        # 商户a退款
        # 商户管理员登录token
        merchant_admin = MerchantAdmin.objects.filter(
            work_merchant_id=self.merchatn_info['a']['merchant_id'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN
        ).first()

        merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            WechatPerson(unionid=merchant_admin.wechat_unionid,
                         subscription_openid=merchant_admin.wechat_openid
                         ))
        transaction_step = TransactionStep(self)
        resp = transaction_step.alipay_refund(merchant_admin_token, payment_info['serial_number'])
        self.assertEqual(resp.json(), {})

        # 退款成功，用户查看其优惠券未消失，商户b卡券已领三张
        resp_json = alipay_clent_step.get_coupons(alipay_person_access_token)
        self.assertEqual(resp_json, coupons)

        # TODO 商户b管理员登录查看卡券已领三张
        # merchant_admin = MerchantAdmin.objects.get(pk=self.merchatn_info['b']['merchant_id'])
        # merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
        #     WechatPerson(unionid=merchant_admin.wechat_unionid,
        #                  subscription_openid=merchant_admin.wechat_openid
        #                  ))
        # coupon_step = CouponStep(self, merchant_admin_token)
        # resp_json = coupon_step.list()

        # 后台管理员登录查看数据
        system_admin_login_step = LoginStep(self)
        finacial_query_step = FinancialQueryStep(self)
        system_admin_login_step.login(**self.system_admin_info)
        resp = finacial_query_step.get_overview_data()
        self.assertEqual(resp.json(),
                         {'merchant': 3, 'inviter': 3, 'client': 1, 'coupon': 3, 'coupon_used': 0,
                          'payment': {'wechat': 0.0, 'alipay': 0.0, 'total': 0.0}})

        # 用户同意地理位置授权，且用户在商户C的位置。支付成功，获取商户B、C的优惠券共3张
        # 给商户a支付10元给商户
        money = 10 * 100
        alipay_payment_step = AlipayPaymentSteps(alipay_person_access_token)
        place_order_resp_json = alipay_payment_step.place_order(
            self.merchatn_info['a']['merchant_id'], money, None)
        print(place_order_resp_json)

        # 支付宝支付成功回调
        resp = alipay_payment_step.payment_callback(dynasettings.ALIPAY_APP_ID,
                                                    alipay_person_userid,
                                                    place_order_resp_json['out_trade_no'],
                                                    10 * 100)
        self.assertEqual(resp.content.decode(), '"OK"')

        # 获取优惠券 , 用户在商户C的位置，获取商户b、c的优惠券共3张
        resp_json = SharedPaySteps(alipay_person['access_token']).poll_result(
            place_order_resp_json['out_trade_no'],
            self.merchatn_info['c']['db_instance'].location_lon,
            self.merchatn_info['c']['db_instance'].location_lat,
            5.0)
        payment_info = resp_json['payment']
        self.assertEqual(payment_info['serial_number'], place_order_resp_json['out_trade_no'])
        self.assertEqual(payment_info['status'], config.PAYMENT_STATUS['FROZEN'])
        self.assertEqual(payment_info['order_price'], money)
        coupons = resp_json['coupons']
        self.assertEqual(len(coupons), 3)
        for coupon in coupons:
            self.assertEqual('商户a', coupon['originator_merchant'])
            self.assertIn(coupon['rule']['merchant']['name'], ['商户b', '商户c'])

        # 后台查看
        resp = finacial_query_step.get_overview_data()
        print(resp.json())
        self.assertEqual(resp.json(),
                         {'merchant': 3, 'inviter': 3, 'client': 1, 'coupon': 6, 'coupon_used': 0,
                          'payment': {'wechat': 0.0, 'alipay': 10, 'total': 10}})

    def test_user_alipay_use_coupon(self):
        """
         使用优惠券付款
        :return:
        """

        # 用户支付宝支付 向a商户0.01 元后退款"""
        # 用户不同意地理位置授权，支付成功，获取商户B的优惠券共3张

        # 支付宝授权
        alipay_clent_step = ClientSteps()
        alipay_person_userid = str(uuid.uuid4().hex)
        alipay_person = alipay_clent_step.alipay_login(str(uuid.uuid4().hex), alipay_person_userid,
                                                       None)
        alipay_person_access_token = alipay_person['access_token']

        # 给商户a支付0.01元给商户
        money = 1
        alipay_payment_step = AlipayPaymentSteps(alipay_person_access_token)
        place_order_resp_json = alipay_payment_step.place_order(
            self.merchatn_info['a']['merchant_id'], money, None)

        # 支付宝支付成功回调
        resp = alipay_payment_step.payment_callback(dynasettings.ALIPAY_APP_ID,
                                                    alipay_person_userid,
                                                    place_order_resp_json['out_trade_no'],
                                                    1)
        self.assertEqual(resp.content.decode(), '"OK"')

        # 获取优惠券 , 未报告位置，获取三张b的优惠券
        resp_json = SharedPaySteps(alipay_person['access_token']).poll_result(
            place_order_resp_json['out_trade_no'], None, None, None)
        payment_info = resp_json['payment']
        self.assertEqual(payment_info['serial_number'], place_order_resp_json['out_trade_no'])
        self.assertEqual(payment_info['status'], config.PAYMENT_STATUS['FROZEN'])
        self.assertEqual(payment_info['order_price'], money)
        coupons = resp_json['coupons']
        user_coupon_type_dict = dict(buy_20_get_10_reduction=[], buy_30_get_20_reduction=[])
        self.assertEqual(len(coupons), 3)
        for coupon in coupons:
            self.assertEqual('商户b', coupon['rule']['merchant']['name'])
            self.assertEqual('商户a', coupon['originator_merchant'])
            if coupon['discount'] == 1000 and coupon['min_charge'] == 2000:
                user_coupon_type_dict['buy_20_get_10_reduction'].append(coupon['id'])
            elif coupon['discount'] == 2000 and coupon['min_charge'] == 3000:
                user_coupon_type_dict['buy_30_get_20_reduction'].append(coupon['id'])
        self.assertNotEqual(user_coupon_type_dict, dict(buy_20_get_10_reduction=[],
                                                        buy_30_get_20_reduction=[]))

        # 商户a退款
        # 商户管理员登录token
        merchant_admin = MerchantAdmin.objects.filter(
            work_merchant_id=self.merchatn_info['a']['merchant_id'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN
        ).first()
        merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            WechatPerson(unionid=merchant_admin.wechat_unionid,
                         subscription_openid=merchant_admin.wechat_openid
                         ))
        transaction_step = TransactionStep(self)
        resp = transaction_step.alipay_refund(merchant_admin_token, payment_info['serial_number'])
        self.assertEqual(resp.json(), {})

        # 退款成功，用户查看其优惠券未消失，商户b卡券已领三张
        resp_json = alipay_clent_step.get_coupons(alipay_person_access_token,
                                                  uuid=self.merchatn_info['b'][
                                                      'db_instance'].payment_qr_code.uuid)
        self.assertEqual(len(resp_json), 3)

        # 用户向商户b付款30元，使用优惠券满30减20实际付款10元，支付成功后得到3张优惠券，然后商户b退款, 然后支付成功
        # 给商户b支付30元给商户
        money = 30 * 100
        alipay_payment_step = AlipayPaymentSteps(alipay_person_access_token)
        place_order_resp_json = alipay_payment_step.place_order(
            self.merchatn_info['b']['merchant_id'],
            money,
            user_coupon_type_dict['buy_30_get_20_reduction'][0])
        print(place_order_resp_json)
        # 支付宝支付成功回调
        resp = alipay_payment_step.payment_callback(dynasettings.ALIPAY_APP_ID,
                                                    alipay_person_userid,
                                                    place_order_resp_json['out_trade_no'],
                                                    1)
        self.assertEqual(resp.content.decode(), '"OK"')

        # 获取优惠券 , 未报告位置，获取三张的优惠券
        resp_json = SharedPaySteps(alipay_person['access_token']).poll_result(
            place_order_resp_json['out_trade_no'], None, None, None)
        payment_info = resp_json['payment']
        self.assertEqual(payment_info['serial_number'], place_order_resp_json['out_trade_no'])
        self.assertEqual(payment_info['status'], config.PAYMENT_STATUS['FROZEN'])
        self.assertEqual(payment_info['order_price'], money)
        coupons = resp_json['coupons']
        self.assertEqual(len(coupons), 3)

        # 支付成功，查看该用户在商户b的优惠券是否减少一张
        resp_json = alipay_clent_step.get_coupons(alipay_person_access_token,
                                                  uuid=self.merchatn_info['b'][
                                                      'db_instance'].payment_qr_code.uuid)
        temp = 0
        for coupon in resp_json:
            if coupon['discount'] == 2000 and coupon['min_charge'] == 3000:
                temp = temp + 1
        self.assertEqual(temp + 1, len(user_coupon_type_dict['buy_30_get_20_reduction']))
        # self.assertEqual(resp_json, coupons)

        # 商户b退款
        # 商户管理员登录token
        merchant_admin = MerchantAdmin.objects.filter(
            work_merchant_id=self.merchatn_info['b']['merchant_id'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN
        ).first()

        merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            WechatPerson(unionid=merchant_admin.wechat_unionid,
                         subscription_openid=merchant_admin.wechat_openid
                         ))
        transaction_step = TransactionStep(self)
        resp = transaction_step.alipay_refund(merchant_admin_token, payment_info['serial_number'])
        self.assertEqual(resp.json(), {})
        # 退款成功，用户查看其优惠券未消失(退款退回一张优惠券)
        resp_json = alipay_clent_step.get_coupons(alipay_person_access_token,
                                                  uuid=self.merchatn_info['b'][
                                                      'db_instance'].payment_qr_code.uuid)
        user_coupon_type_dict = dict(buy_20_get_10_reduction=[], buy_30_get_20_reduction=[])
        self.assertEqual(len(resp_json), 3)
        for coupon in resp_json:
            self.assertEqual('商户b', coupon['rule']['merchant']['name'])
            self.assertEqual('商户a', coupon['originator_merchant'])
            if coupon['discount'] == 1000 and coupon['min_charge'] == 2000:
                user_coupon_type_dict['buy_20_get_10_reduction'].append(coupon['id'])
            elif coupon['discount'] == 2000 and coupon['min_charge'] == 3000:
                user_coupon_type_dict['buy_30_get_20_reduction'].append(coupon['id'])
        self.assertNotEqual(user_coupon_type_dict,
                            dict(buy_20_get_10_reduction=[], buy_30_get_20_reduction=[]))

        # 用户再次支付30向商户b付款30元，使用优惠券满30减20实际付款10元，支付成功后得到3张优惠券，

        money = 30 * 100
        alipay_payment_step = AlipayPaymentSteps(alipay_person_access_token)
        place_order_resp_json = alipay_payment_step.place_order(
            self.merchatn_info['b']['merchant_id'],
            money,
            user_coupon_type_dict['buy_30_get_20_reduction'][0])
        # 支付宝支付成功回调
        resp = alipay_payment_step.payment_callback(dynasettings.ALIPAY_APP_ID,
                                                    alipay_person_userid,
                                                    place_order_resp_json['out_trade_no'],
                                                    1)
        self.assertEqual(resp.content.decode(), '"OK"')
        # 获取优惠券 , 未报告位置，获取三张的优惠券
        resp_json = SharedPaySteps(alipay_person['access_token']).poll_result(
            place_order_resp_json['out_trade_no'], None, None, None)
        payment_info = resp_json['payment']
        self.assertEqual(payment_info['serial_number'], place_order_resp_json['out_trade_no'])
        self.assertEqual(payment_info['status'], config.PAYMENT_STATUS['FROZEN'])
        self.assertEqual(payment_info['order_price'], money)
        # 解冻账单成功
        resp_json = SharedPaySteps(None).unfreeze_immediately()
        print(resp_json)
        self.assertEqual(resp_json, "OK")

        # 商户a查看引流收益
        # 商户管理员登录token TODO 接口更新
        # merchant_admin = MerchantAdmin.objects.get(pk=self.merchatn_info['a']['merchant_id'])
        # merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
        #     WechatPerson(unionid=merchant_admin.wechat_unionid,
        #                  subscription_openid=merchant_admin.wechat_openid
        #                  ))
        # merchant_step = MerchantStep(self, merchant_admin_token)
        # resp = merchant_step.statistics()
        # print(resp.json())
        # 邀请人查看引流收益
        inviter_get_userinfo_step = GetUserInfoStep()
        resp, _ = inviter_get_userinfo_step.go(token=self.inviter_info['b']['token'])
        resp_json = resp.json()
        self.assertEqual(resp_json['user_name'], '邀请人2')
        self.assertEqual(resp_json['using_invited_merchants_num'], 1)
        self.assertEqual(resp_json['total_bonus'], 10)
        # 管理后台查看数据
        system_admin_login_step = LoginStep(self)
        finacial_query_step = FinancialQueryStep(self)
        system_admin_login_step.login(**self.system_admin_info)
        resp = finacial_query_step.get_overview_data()
        self.assertEqual(resp.json(), {'merchant': 3, 'inviter': 3, 'client': 1,
                                       'coupon': 9, 'coupon_used': 1,
                                       'payment': {'wechat': 0.0, 'alipay': 10.0, 'total': 10.0}})
