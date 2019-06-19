#      File: test_transaction_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/29
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import re

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from common.model_manager.transaction_manager import TransactionModelManager, TransactionManager
from common.model_manager.utils import set_amount
from config import TRANSACTION_TYPE, WITHDRAW_STATUS, PAY_CHANNELS, PAYMENT_STATUS, WITHDRAW_TYPE, SYSTEM_USER_STATUS, \
    MERCHANT_ADMIN_TYPES, SETTLEMENT_STATUS
from test.unittest.fake_factory import PayunionFactory
from test.utils import render


class Config:
    withdraw = -90
    wechat_settlement = -40
    alipay_settlement = -50
    receive = 100.1
    share = 1.01
    jan = timezone.datetime(year=2018, month=1, day=1)
    feb = timezone.datetime(year=2018, month=2, day=1)
    mar = timezone.datetime(year=2018, month=3, day=1)
    apr = timezone.datetime(year=2018, month=4, day=1)
    may = timezone.datetime(year=2018, month=5, day=1)


class TestTransactionModelManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.merchant_admin = cls.factory.create_merchant_admin()
        cls.merchant = cls.merchant_admin.work_merchant
        cls.account = cls.merchant.account
        cls.manager = TransactionModelManager()

    def _create_transactions(self):
        # 1月2月3月5月, 每月分别创建2条 营业额/提现/分成transaction
        share_merchant = self.factory.create_merchant(name='引流到达的商户')
        for time in (Config.jan, Config.feb, Config.mar, Config.may):
            for i in range(2):
                # 提现
                withdraw = self.factory.create_withdraw(
                    withdraw_type=WITHDRAW_TYPE.ALIPAY if i % 2 else WITHDRAW_TYPE.WECHAT,
                    account=self.account,
                    amount=set_amount(-Config.withdraw),
                    datetime=time)
                self.factory.create_transaction(
                    content_object=withdraw,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.withdraw),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_WITHDRAW'])

                # 企业商户结算
                settlement = self.factory.create_settlement(
                    status=SETTLEMENT_STATUS.FINISHED,
                    account=self.account,
                    finished_datetime=time,
                    wechat_amount=set_amount(-Config.wechat_settlement),
                    alipay_amount=set_amount(-Config.alipay_settlement),
                )
                self.factory.create_transaction(
                    content_object=settlement,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.withdraw / 2),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'])
                self.factory.create_transaction(
                    content_object=settlement,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.withdraw / 2),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_ALIPAY_SETTLEMENT'])

                coupon_rule = self.factory.create_coupon_rule(discount=set_amount(100), min_charge=set_amount(300))

                # 支付成功
                coupon = self.factory.create_coupon(rule=coupon_rule)
                payment = self.factory.create_payment(
                    merchant=self.merchant,
                    datetime=time,
                    coupon=coupon,
                    status=PAYMENT_STATUS['FINISHED']
                )
                self.factory.create_transaction(
                    content_object=payment,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.receive),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])

                # 退款
                coupon = self.factory.create_coupon(rule=coupon_rule)
                payment = self.factory.create_payment(
                    merchant=self.merchant,
                    datetime=time,
                    coupon=coupon,
                    status=PAYMENT_STATUS['REFUND']
                )
                self.factory.create_transaction(
                    content_object=payment,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.receive),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])
                self.factory.create_transaction(
                    content_object=payment,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(-Config.receive),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'])

                # 引流分成
                coupon_rule = self.factory.create_coupon_rule(merchant=self.merchant)
                share = self.factory.create_payment(
                    coupon=self.factory.create_coupon(rule=coupon_rule, originator_merchant=self.merchant),
                    datetime=time, merchant=share_merchant)
                self.factory.create_transaction(
                    content_object=share,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.share),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])

    def test_serialize(self):

        # test empty transactions serialize
        # page=1, page_size=20
        query_set = self.manager.list_merchant_transaction(merchant=self.merchant)[:20]
        result = self.manager.serialize(transactions=query_set)
        self.assertEqual(result, [])

        # test transactions serialize
        self._create_transactions()

        # page=1, page_size=20
        query_set = self.manager.list_merchant_transaction(merchant=self.merchant)[:20]
        result = self.manager.serialize(transactions=query_set)

        def check_result(data):
            for month_data in data:
                if month_data['month'] == '2018/04':
                    self.assertEqual(month_data['cur_page_transactions'], [])
                    self.assertEqual(month_data['turnover'], 0)
                    self.assertEqual(month_data['originator_earning'], 0)
                    self.assertEqual(month_data['withdraw'], 0)
                else:
                    # 获取的是该月总额
                    self.assertEqual(month_data['turnover'], Config.receive * 2)
                    self.assertEqual(month_data['originator_earning'], Config.share * 2)
                    self.assertEqual(month_data['withdraw'], -Config.withdraw * 2)
                    # 检查每笔订单详细展示
                    for transaction in month_data['cur_page_transactions']:
                        self.assertIsInstance(transaction['id'], int)
                        self.assertIn(transaction['title'], (
                            '余额提现 - 到支付宝余额', '余额提现 - 到微信零钱', '微信支付', '支付宝支付',
                            '微信支付 - 优惠账单', '支付宝支付 - 优惠账单', '引流到达的商户', '账单结算'
                        ))
                        self.assertIn(transaction['desc'], ('[其他]', '[普通]', '[满300减100优惠券]'))
                        self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
                        self.assertIn(transaction['status'], ('已完成', '已退款', '退款中', '退款失败', '处理中',
                                                              '已失败', '已结算', '结算中', ''))
                        self.assertIn(transaction['transaction_type'],
                                      ('normal', 'discount', 'withdraw', 'original_earning'))

        check_result(result)

        # page=2, page_size=20
        query_set = self.manager.list_merchant_transaction(merchant=self.merchant)[20:40]
        result = self.manager.serialize(transactions=query_set)

        check_result(result)


class TestTransactionManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.account = cls.factory.create_account(
            bank_name='工商银行成都建设路支行',
            bank_card_number='7778889990123',
            real_name='鹏飞'
        )
        cls.merchant = cls.factory.create_merchant(account=cls.account)

    def _create_transactions(self):
        # 1月2月3月4月 一个月对应创建一条 提现/普通订单/优惠券订单/分成transaction
        # 提现
        self.withdraw = self.factory.create_withdraw(
            withdraw_type=WITHDRAW_TYPE.ALIPAY,
            account=self.account,
            amount=set_amount(Config.withdraw),
            datetime=Config.jan,
            status=WITHDRAW_STATUS['PROCESSING']
        )
        self.withdraw_transaction = self.factory.create_transaction(
            content_object=self.withdraw,
            account=self.account,
            datetime=Config.jan,
            amount=set_amount(Config.withdraw),
            transaction_type=TRANSACTION_TYPE['MERCHANT_WITHDRAW'])

        # 普通订单
        self.payment_without_coupon = self.factory.create_payment(
            merchant=self.merchant,
            datetime=Config.feb,
            pay_channel=PAY_CHANNELS['WECHAT'],
            note='这是一个普通订单',
            status=PAYMENT_STATUS['REFUND'],
            order_price=set_amount(Config.receive),
        )
        self.payment_without_coupon_transaction = self.factory.create_transaction(
            content_object=self.payment_without_coupon,
            account=self.account,
            datetime=Config.feb,
            amount=set_amount(Config.receive),
            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])

        # 优惠券订单
        coupon = self.factory.create_coupon(
            rule=self.factory.create_coupon_rule(discount=set_amount(100), min_charge=set_amount(300)))
        self.payment_with_coupon = self.factory.create_payment(
            merchant=self.merchant,
            datetime=Config.mar,
            pay_channel=PAY_CHANNELS['ALIPAY'],
            note='这是一个优惠券订单',
            status=PAYMENT_STATUS['FROZEN'],
            coupon=coupon,
            order_price=set_amount(100 + Config.receive),
            platform_share=set_amount(33),
            inviter_share=set_amount(33),
            originator_share=set_amount(34),
        )
        self.payment_with_coupon_transaction = self.factory.create_transaction(
            content_object=self.payment_with_coupon,
            account=self.account,
            datetime=Config.mar,
            amount=set_amount(Config.receive),
            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
        )

        # 引流收益订单
        share_merchant = self.factory.create_merchant(name='引流到达的商户')
        coupon = self.factory.create_coupon(
            rule=self.factory.create_coupon_rule(discount=set_amount(100), min_charge=set_amount(300)))
        self.share_payment = self.factory.create_payment(
            coupon=coupon,
            datetime=Config.apr, merchant=share_merchant,
            order_price=set_amount(100 + Config.receive),
            platform_share=set_amount(33),
            inviter_share=set_amount(33),
            originator_share=set_amount(34),
            status=PAYMENT_STATUS['FINISHED'],
        )
        self.share_transaction = self.factory.create_transaction(
            content_object=self.share_payment,
            account=self.account,
            datetime=Config.apr + timedelta(hours=2),
            amount=set_amount(Config.share),
            transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])

    def test_detail(self):
        self._create_transactions()

        # 提现
        manager = TransactionManager(self.withdraw_transaction)
        detail = manager.detail
        self.assertEqual(detail, dict(
            id=self.withdraw_transaction.id,
            amount=-Config.withdraw,
            serial_number=self.withdraw.serial_number,
            transaction_type='余额提现',
            withdraw_type=WITHDRAW_TYPE.ALIPAY,
            status=WITHDRAW_STATUS['PROCESSING'],
            create_datetime=render(Config.jan)
        ))

        # 普通订单
        manager = TransactionManager(self.payment_without_coupon_transaction)
        detail = manager.detail
        self.assertEqual(detail, dict(
            id=self.payment_without_coupon_transaction.id,
            amount=Config.receive,
            serial_number=self.payment_without_coupon.serial_number,
            pay_channel=PAY_CHANNELS['WECHAT'],
            create_datetime=render(Config.feb),
            note='这是一个普通订单',
            transaction_type='普通',
            status=PAYMENT_STATUS['REFUND'],
        ))

        # 优惠券订单
        manager = TransactionManager(self.payment_with_coupon_transaction)
        detail = manager.detail

        self.assertEqual(detail, dict(
            id=self.payment_with_coupon_transaction.id,
            amount=Config.receive,
            serial_number=self.payment_with_coupon.serial_number,
            pay_channel=PAY_CHANNELS['ALIPAY'],
            create_datetime=render(Config.mar),
            note='这是一个优惠券订单',
            status=PAYMENT_STATUS['FROZEN'],
            transaction_type='优惠',
            order_price=100 + Config.receive,
            discount=100,
            total_share='99.9%',
            coupon='[满300减100优惠券]',
            coupon_rule_id=self.payment_with_coupon.coupon.rule_id
        ))

        # 引流分成订单
        manager = TransactionManager(self.share_transaction)
        detail = manager.detail
        self.assertEqual(detail, dict(
            id=self.share_transaction.id,
            amount=Config.share,
            status=PAYMENT_STATUS['FINISHED'],
            merchant_name='引流到达的商户',
            serial_number=self.share_payment.serial_number,
            transaction_type='引流收益',
            price_after_discount=Config.receive,
            merchant_share='33.96%',
            create_datetime=render(Config.apr),
            receive_datetime=render(Config.apr + timedelta(hours=2)),
        ))
