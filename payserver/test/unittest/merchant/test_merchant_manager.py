#      File: test_merchant_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/22
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from contextlib import contextmanager
from functools import partial

from django.test import TestCase
from django.utils.timezone import timedelta
from django.utils import timezone

from config import TRANSACTION_TYPE, COUPON_STATUS, SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES, PAYMENT_STATUS, \
    REFUND_STATUS
from common.model_manager.merchant_manager import MerchantManager
from common.model_manager.utils import set_amount
from test.unittest.fake_factory import PayunionFactory


class TestMerchantManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.account = cls.factory.create_account(
            balance=set_amount(1000.00),
            withdrawable_balance=set_amount('500.05'),
            alipay_balance=set_amount(2000),
            alipay_withdrawable_balance=set_amount(0.99),
            bank_card_number='1234567890123'
        )
        cls.merchant = cls.factory.create_merchant(
            name='就是这个公司',
            account=cls.account,
            day_begin_minute=8 * 60,  # 商户订单日结时间设置为08:00
        )
        cls.merchant_admin = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN']

        )
        cls.manager = MerchantManager(cls.merchant)

        # create cashiers
        cls.normal_cashier_a = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.normal_cashier_b = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.other_merchant_cashier = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.disabled_cashier = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['DISABLED'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

    @contextmanager
    def not_change_account(self):
        old_balance = self.account.balance
        old_withdrawable_balance = self.account.withdrawable_balance
        old_alipay_balance = self.account.alipay_balance
        old_alipay_withdrawable_balance = self.account.alipay_withdrawable_balance
        yield
        self.account.balance = old_balance
        self.account.withdrawable_balance = old_withdrawable_balance
        self.account.alipay_balance = old_alipay_balance
        self.account.alipay_withdrawable_balance = old_alipay_withdrawable_balance
        self.account.save()

    def test_wechat_account_balance(self):
        self.assertEqual(self.manager.account_wechat_balance, 1000)

    def test_account_wechat_withdraw_balance(self):
        # 能正确查询到商户账户微信可提现余额
        self.assertEqual(self.manager.account_wechat_withdraw_balance, 500.05)

        # 修改余额为0.01后不足微信最小可提现余额, 可提现余额逻辑显示为0.01(前端显示为0)
        with self.not_change_account():
            self.account.withdrawable_balance = set_amount('0.01')
            self.account.save()
            self.assertEqual(self.manager.account_wechat_withdraw_balance, 0.01)

    def test_alipay_account_balance(self):
        self.assertEqual(self.manager.account_alipay_balance, 2000)

    def test_alipay_wechat_withdraw_balance(self):
        # 不足支付宝最小可提现余额, 可提现余额逻辑显示为0
        self.assertEqual(self.manager.account_alipay_withdraw_balance, 0.99)

        # 修改余额为100.3后能正确查询到
        with self.not_change_account():
            self.account.alipay_withdrawable_balance = set_amount('100.3')
            self.account.save()
            self.assertEqual(self.manager.account_alipay_withdraw_balance, 100.3)

    def test_merchant_admin(self):
        merchant_admin = self.manager.merchant_admin
        self.assertEqual(merchant_admin, self.merchant_admin)

    def test_merchant_statistics(self):

        first_day = timezone.now().replace(year=2018, month=1, day=1, hour=9)
        second_day = timezone.now().replace(year=2018, month=1, day=2, hour=9)

        # 1. 创建一笔退款订单
        refund_payment = self.factory.create_payment(
            datetime=second_day,
            merchant=self.merchant,
            order_price=set_amount(100),
            status=PAYMENT_STATUS.REFUND
        )

        # 退款订单
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
            datetime=second_day,
            account=self.account,
            amount=set_amount(100),
            content_object=refund_payment
        )
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_REFUND,
            datetime=second_day,
            account=self.account,
            amount=-set_amount(100),
            content_object=self.factory.create_refund(
                datetime=second_day, status=REFUND_STATUS.FINISHED, payment=refund_payment)
        )

        # 2. 两天分别创建一笔未支付订单, 一笔优惠订单, 一笔普通订单, 一笔引流收益
        for datetime_ in (first_day, second_day):
            # 未支付订单
            self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.UNPAID,
                merchant=self.merchant,
                order_price=set_amount(100),
            )

            # 优惠券订单
            coupon = self.factory.create_coupon(
                discount=set_amount(10),
                min_charge=set_amount(100),
                status=COUPON_STATUS.USED,
                use_datetime=datetime_,
            )
            use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(110),
                coupon=coupon,
                platform_share=set_amount(3),
                originator_share=set_amount(1),
                inviter_share=set_amount(1)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(95),
                content_object=use_coupon_payment,
            )

            # 普通订单
            not_use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(100),
                platform_share=set_amount(0),
                originator_share=set_amount(0),
                inviter_share=set_amount(0)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(100),
                content_object=not_use_coupon_payment,
            )

            # 引流收益
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(1),
            )

        # 3. 检查第二日
        second_day_begin = second_day.replace(hour=0, minute=0, second=0, microsecond=0)
        result = self.manager.merchant_business_report(
            datetime_start=second_day_begin,
            datetime_end=second_day_begin + timedelta(days=1)
        )
        self.assertEqual(result, {'turnover': 200,
                                  'originator_expenditure': 5,
                                  'originator_earning': 1,
                                  'payment': {'use_coupon': 1, 'not_use_coupon': 2}})

        # 4. 检查第一日
        first_day_begin = first_day.replace(hour=0, minute=0, second=0, microsecond=0)
        result = self.manager.merchant_business_report(
            datetime_start=first_day_begin,
            datetime_end=first_day_begin + timedelta(days=1)
        )
        self.assertEqual(result, {'turnover': 200,
                                  'originator_expenditure': 5,
                                  'originator_earning': 1,
                                  'payment': {'use_coupon': 1, 'not_use_coupon': 1}})

    def test_merchant_employer_num(self):
        """收银员数量"""
        self.assertEqual(self.manager.employer_num, 3)

        self.factory.create_merchant_admin(number=5, work_merchant=self.merchant)
        self.assertEqual(self.manager.employer_num, 8)

        self.factory.create_merchant_admin(number=5, work_merchant=self.merchant)
        self.assertEqual(self.manager.employer_num, 13)

        self.factory.create_merchant_admin(5)
        self.assertEqual(self.manager.employer_num, 13)

    def test_merchant_earning_list_by_day(self):
        first_day = timezone.now().replace(year=2018, month=1, day=1, hour=9)
        second_day = timezone.now().replace(year=2018, month=1, day=2, hour=9)
        third_day = timezone.now().replace(year=2018, month=1, day=4, hour=9)

        first_day_begin = first_day.replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. 创建一笔退款订单
        refund_payment = self.factory.create_payment(
            datetime=second_day,
            merchant=self.merchant,
            order_price=set_amount(100),
            status=PAYMENT_STATUS.REFUND
        )

        # 退款订单
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
            datetime=second_day,
            account=self.account,
            amount=set_amount(100),
            content_object=refund_payment
        )
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_REFUND,
            datetime=second_day,
            account=self.account,
            amount=-set_amount(100),
            content_object=self.factory.create_refund(
                datetime=second_day, status=REFUND_STATUS.FINISHED, payment=refund_payment)
        )

        # 2. 三天分别创建一笔未支付订单, 一笔优惠订单, 一笔普通订单, 一笔引流收益
        for datetime_ in (first_day, second_day, third_day):
            # 未支付订单
            self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.UNPAID,
                merchant=self.merchant,
                order_price=set_amount(100),
            )

            # 优惠券订单
            coupon = self.factory.create_coupon(
                discount=set_amount(10),
                min_charge=set_amount(100),
                status=COUPON_STATUS.USED,
                use_datetime=datetime_,
            )
            use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(110),
                coupon=coupon,
                platform_share=set_amount(3),
                originator_share=set_amount(1),
                inviter_share=set_amount(1)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(95),
                content_object=use_coupon_payment,
            )

            # 普通订单
            not_use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(100),
                platform_share=set_amount(0),
                originator_share=set_amount(0),
                inviter_share=set_amount(0)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(100),
                content_object=not_use_coupon_payment,
            )

            # 引流收益
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(1),
            )

        result = self.manager.merchant_earning_list_by_day(
            date_start=first_day_begin.date() - timedelta(days=1),
            date_end=first_day_begin.date() + timedelta(days=5)
        )

        self.assertEqual(
            result,
            [{'date': '2017-12-31', 'amount': 0},
             {'date': '2018-01-01', 'amount': 195 + 1},
             {'date': '2018-01-02', 'amount': 195 + 1},
             {'date': '2018-01-03', 'amount': 0},
             {'date': '2018-01-04', 'amount': 195 + 1},
             {'date': '2018-01-05', 'amount': 0},
             {'date': '2018-01-06', 'amount': 0}]
        )

    def test_get_cashier(self):
        not_exist_id = 100000

        self.assertEqual(self.manager.get_cashier(self.normal_cashier_a.id), self.normal_cashier_a)
        self.assertEqual(self.manager.get_cashier(self.normal_cashier_b.id), self.normal_cashier_b)
        self.assertEqual(self.manager.get_cashier(self.other_merchant_cashier.id), None)
        self.assertEqual(self.manager.get_cashier(self.disabled_cashier.id), None)
        self.assertEqual(self.manager.get_cashier(not_exist_id), None)

    def test_cashiers(self):
        cashiers = self.manager.cashiers
        self.assertEqual(len(cashiers), 2)
        self.assertEqual(set(cashiers), {self.normal_cashier_a, self.normal_cashier_b})
