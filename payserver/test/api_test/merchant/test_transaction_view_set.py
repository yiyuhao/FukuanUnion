#      File: test_transaction_view_set.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/28
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import re

from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.error_handler import MerchantError
from common.model_manager.utils import set_amount
from config import TRANSACTION_TYPE, WITHDRAW_STATUS, PAY_CHANNELS, PAYMENT_STATUS, MERCHANT_STATUS, WITHDRAW_TYPE, \
    SETTLEMENT_STATUS
from test.api_test.merchant.utils import MerchantLoginedMixin
from test.unittest.fake_factory import PayunionFactory
from test.utils import NonFieldError
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


class TestTransactionViewSet(MerchantLoginedMixin, APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.account = cls.factory.create_account(
            bank_name='工商银行成都建设路支行',
            bank_card_number='7778889990123',
            real_name='鹏飞'
        )
        cls.merchant = cls.factory.create_merchant(
            account=cls.account,
            day_begin_minute=8 * 60,
            status=MERCHANT_STATUS['USING']
        )
        cls.merchant_admin = cls.factory.create_merchant_admin(work_merchant=cls.merchant)

        # 创建token并缓存, 绕过登录
        super(TestTransactionViewSet, cls).setUpTestData()

    def _create_transactions(self):
        # 1月2月3月4月5月 一个月对应创建一条 提现/普通订单/优惠券订单/分成/结算transaction
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
            rule=self.factory.create_coupon_rule(discount=set_amount(100),
                                                 min_charge=set_amount(300)))
        self.payment_with_coupon = self.factory.create_payment(
            merchant=self.merchant,
            datetime=Config.mar,
            pay_channel=PAY_CHANNELS['ALIPAY'],
            note='这是一个优惠券订单',
            status=PAYMENT_STATUS['FROZEN'],
            coupon=coupon,
            order_price=set_amount(200.1),
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
            rule=self.factory.create_coupon_rule(discount=set_amount(100),
                                                 min_charge=set_amount(300)))
        self.share_payment = self.factory.create_payment(
            coupon=coupon,
            datetime=Config.apr,
            status=PAYMENT_STATUS['FINISHED'],
            merchant=share_merchant,
            order_price=set_amount(200.1),
            platform_share=set_amount(33),
            inviter_share=set_amount(33),
            originator_share=set_amount(34),
        )
        self.share_transaction = self.factory.create_transaction(
            content_object=self.share_payment,
            account=self.account,
            datetime=Config.apr + timedelta(hours=2),
            amount=set_amount(Config.share),
            transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])

        # 企业商户结算
        self.settlement = self.factory.create_settlement(
            status=SETTLEMENT_STATUS.FINISHED,
            account=self.account,
            datetime=Config.may,
            finished_datetime=Config.may + timedelta(hours=1),
            wechat_amount=set_amount(-Config.wechat_settlement),
            alipay_amount=set_amount(-Config.alipay_settlement),
        )
        self.settlement_transaction = self.factory.create_transaction(
            content_object=self.settlement,
            account=self.account,
            datetime=Config.may,
            amount=set_amount(Config.withdraw / 2),
            transaction_type=TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'])
        self.factory.create_transaction(
            content_object=self.settlement,
            account=self.account,
            datetime=Config.may,
            amount=set_amount(Config.withdraw / 2),
            transaction_type=TRANSACTION_TYPE['MERCHANT_ALIPAY_SETTLEMENT'])

    def test_transaction_list(self):
        url = reverse('transaction-list')

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

                coupon_rule = self.factory.create_coupon_rule(discount=set_amount(100),
                                                              min_charge=set_amount(300))

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
                    coupon=self.factory.create_coupon(rule=coupon_rule,
                                                      originator_merchant=self.merchant),
                    datetime=time, merchant=share_merchant)
                self.factory.create_transaction(
                    content_object=share,
                    account=self.account,
                    datetime=time,
                    amount=set_amount(Config.share),
                    transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])

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

        # 第一页
        response = self.client.get(url, dict(page=1), Token=self.token)
        first_page_resp_json = response.json()
        for month_data in first_page_resp_json['results']:
            if month_data['month'] == '2018/04':
                self.assertEqual(month_data['cur_page_transactions'], [])
                self.assertEqual(month_data['turnover'], 0)
                self.assertEqual(month_data['originator_earning'], 0)
                self.assertEqual(month_data['withdraw'], 0)
            else:
                # 获取的是该月总额
                self.assertEqual(month_data['turnover'], Config.receive * 2)
                self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
                self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
                # 检查每笔订单详细展示
                for transaction in month_data['cur_page_transactions']:
                    self.assertIsInstance(transaction['id'], int)
                    self.assertIn(transaction['title'], (
                        '余额提现 - 到支付宝余额', '余额提现 - 到微信零钱', '微信支付', '支付宝支付',
                        '微信支付 - 优惠账单', '支付宝支付 - 优惠账单', '引流到达的商户', '账单结算',
                    ))
                    self.assertIn(transaction['desc'], ('[其他]', '[普通]', '[满300减100优惠券]'))
                    self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
                    self.assertIn(transaction['status'], ('已完成', '已退款', '退款中', '退款失败',
                                                          '处理中', '已失败', '已结算', '结算中', ''))
                    self.assertIn(transaction['transaction_type'],
                                  ('normal', 'discount', 'withdraw', 'original_earning'))

        # 第二页
        response = self.client.get(url, dict(page=2, type='all'), Token=self.token)
        resp_json = response.json()
        self.assertEqual(len(resp_json['results']), 2)  # 有两个月数据
        month_data = resp_json['results'][0]

        self.assertEqual(month_data['turnover'], float(Config.receive * 2))
        self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
        self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
        for transaction in month_data['cur_page_transactions']:
            self.assertIsInstance(transaction['id'], int)
            self.assertIn(transaction['title'], (
                '余额提现 - 到支付宝余额', '余额提现 - 到微信零钱', '微信支付', '支付宝支付',
                '微信支付 - 优惠账单', '支付宝支付 - 优惠账单', '引流到达的商户', '账单结算',
            ))
            self.assertIn(transaction['desc'], ('[其他]', '[普通]', '[满300减100优惠券]'))
            self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
            self.assertIn(transaction['status'], ('已完成', '已退款', '退款中', '退款失败', '处理中',
                                                  '已失败', '已结算', '结算中', ''))
            self.assertIn(transaction['transaction_type'], ('normal', 'discount', 'withdraw', 'original_earning'))

        # 第一页 营业额
        response = self.client.get(url, dict(page=1, type='turnover'), Token=self.token)
        resp_json = response.json()
        for month_data in resp_json['results']:
            if month_data['month'] == '2018/04':
                self.assertEqual(month_data['cur_page_transactions'], [])
                self.assertEqual(month_data['turnover'], 0)
                self.assertEqual(month_data['originator_earning'], 0)
                self.assertEqual(month_data['withdraw'], 0)
            else:
                # 每月2笔营业额
                self.assertEqual(len(month_data['cur_page_transactions']), 4)
                # 获取的是该月总额
                self.assertEqual(month_data['turnover'], float(Config.receive * 2))
                self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
                self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
                # 检查每笔订单详细展示
                for transaction in month_data['cur_page_transactions']:
                    self.assertIsInstance(transaction['id'], int)
                    self.assertIn(transaction['title'], (
                        '微信支付', '支付宝支付', '微信支付 - 优惠账单', '支付宝支付 - 优惠账单'
                    ))
                    self.assertEqual(transaction['desc'], '[满300减100优惠券]')
                    self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
                    self.assertIsInstance(transaction['amount'], float)
                    self.assertIn(transaction['status'], ('已退款', '退款中', '退款失败', ''))
                    self.assertIn(transaction['transaction_type'], ('normal', 'discount'))

        # 第一页 引流收益
        response = self.client.get(url, dict(page=1, type='originator_earning'), Token=self.token)
        resp_json = response.json()
        for month_data in resp_json['results']:
            if month_data['month'] == '2018/04':
                self.assertEqual(month_data['cur_page_transactions'], [])
                self.assertEqual(month_data['turnover'], 0)
                self.assertEqual(month_data['originator_earning'], 0)
                self.assertEqual(month_data['withdraw'], 0)
            else:
                # 每月2笔引流收益
                self.assertEqual(len(month_data['cur_page_transactions']), 2)
                # 获取的是该月总额
                self.assertEqual(month_data['turnover'], float(Config.receive * 2))
                self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
                self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
                # 检查每笔订单详细展示
                for transaction in month_data['cur_page_transactions']:
                    self.assertIsInstance(transaction['id'], int)
                    self.assertEqual(transaction['title'], '引流到达的商户')
                    self.assertEqual(transaction['desc'], '[其他]')
                    self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
                    self.assertEqual(transaction['amount'], 1.01)
                    self.assertIn(transaction['status'], ('已退款', '退款中', '退款失败', ''))
                    self.assertEqual(transaction['transaction_type'], 'original_earning')

        # 第一页 提现
        response = self.client.get(url, dict(page=1, type='withdraw'), Token=self.token)
        resp_json = response.json()
        for month_data in resp_json['results']:
            if month_data['month'] == '2018/04':
                self.assertEqual(month_data['cur_page_transactions'], [])
                self.assertEqual(month_data['turnover'], 0)
                self.assertEqual(month_data['originator_earning'], 0)
                self.assertEqual(month_data['withdraw'], 0)
            else:
                # 每月2笔提现账单
                self.assertEqual(len(month_data['cur_page_transactions']), 2)
                # 获取的是该月总额
                self.assertEqual(month_data['turnover'], float(Config.receive * 2))
                self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
                self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
                # 检查每笔订单详细展示
                for transaction in month_data['cur_page_transactions']:
                    self.assertIsInstance(transaction['id'], int)
                    self.assertIn(transaction['title'], ('余额提现 - 到支付宝余额', '余额提现 - 到微信零钱'))
                    self.assertEqual(transaction['desc'], '[其他]')
                    self.assertTrue(re.match('0[1-5]-01 00:00', transaction['datetime']))
                    self.assertEqual(transaction['amount'], -Config.withdraw)
                    self.assertIn(transaction['status'], ('已完成', '处理中', '已失败', ''))
                    self.assertEqual(transaction['transaction_type'], 'withdraw')

        # 第一页 结算账单
        response = self.client.get(url, dict(page=1, type='settlement'), Token=self.token)
        resp_json = response.json()
        for month_data in resp_json['results']:
            if month_data['month'] == '2018/04':
                self.assertEqual(month_data['cur_page_transactions'], [])
                self.assertEqual(month_data['turnover'], 0)
                self.assertEqual(month_data['originator_earning'], 0)
                self.assertEqual(month_data['withdraw'], 0)
            else:
                # 每月2笔结算账单
                self.assertEqual(len(month_data['cur_page_transactions']), 2)
                # 获取的是该月总额
                self.assertEqual(month_data['turnover'], float(Config.receive * 2))
                self.assertEqual(month_data['originator_earning'], float(Config.share * 2))
                self.assertEqual(month_data['withdraw'], -float(Config.withdraw * 2))
                # 检查每笔订单详细展示
                for transaction in month_data['cur_page_transactions']:
                    self.assertIsInstance(transaction['id'], int)
                    self.assertIn(transaction['title'], ('账单结算',))
                    self.assertEqual(transaction['desc'], '[其他]')
                    self.assertTrue(re.match('0[1235]-01 00:00', transaction['datetime']))
                    self.assertEqual(transaction['amount'], -Config.withdraw)
                    self.assertIn(transaction['status'], ('已结算',))
                    self.assertEqual(transaction['transaction_type'], 'withdraw')

        # 无数据页
        response = self.client.get(url, dict(page=3), Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json['detail'], '无效页面。')
        self.assertEqual(resp_json['error_code'], 'not_found')

        # 请求不带page参数, 应返回第一页数据
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, first_page_resp_json)

        # 请求参数错误
        response = self.client.get(url, dict(page=1, type='wrong_type'), Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MerchantError.unsupported_transaction_type))

    def test_transaction_retrieve(self):

        self._create_transactions()

        # 提现
        url = reverse('transaction-detail', kwargs=dict(pk=self.withdraw_transaction.id))
        response = self.client.get(url, Token=self.token)
        detail = response.json()
        self.assertEqual(detail, dict(
            id=self.withdraw_transaction.id,
            amount=-Config.withdraw,
            serial_number=self.withdraw.serial_number,
            transaction_type='余额提现',
            withdraw_type=WITHDRAW_TYPE.ALIPAY,
            status=WITHDRAW_STATUS['PROCESSING'],
            create_datetime=render(Config.jan),
        ))

        # 普通订单
        url = reverse('transaction-detail',
                      kwargs=dict(pk=self.payment_without_coupon_transaction.id))
        response = self.client.get(url, Token=self.token, format='json')
        detail = response.json()
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

        # 优惠券订单 (可同时通过transaction.id 或payment.serial_number查询)
        for pk in (self.payment_with_coupon_transaction.id, self.payment_with_coupon.serial_number):
            url = reverse('transaction-detail', kwargs=dict(pk=pk))
            response = self.client.get(url, Token=self.token)
            detail = response.json()

            # 通过serial_number查询订单
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
        url = reverse('transaction-detail', kwargs=dict(pk=self.share_transaction.id))
        response = self.client.get(url, Token=self.token)
        detail = response.json()
        self.assertEqual(detail, dict(
            id=self.share_transaction.id,
            amount=Config.share,
            merchant_name='引流到达的商户',
            status=PAYMENT_STATUS['FINISHED'],
            serial_number=self.share_payment.serial_number,
            transaction_type='引流收益',
            price_after_discount=Config.receive,
            merchant_share='33.96%',
            create_datetime=render(Config.apr),
            receive_datetime=render(Config.apr + timedelta(hours=2)),
        ))

        # 结算订单
        url = reverse('transaction-detail', kwargs=dict(pk=self.settlement_transaction.id))
        response = self.client.get(url, Token=self.token)
        detail = response.json()
        self.assertEqual(detail, dict(
            id=self.settlement_transaction.id,
            amount=-Config.withdraw,
            serial_number=self.settlement.serial_number,
            transaction_type='结算账单',
            status=SETTLEMENT_STATUS['FINISHED'],
            create_datetime=render(Config.may),
            receive_datetime=render(Config.may + timedelta(hours=1))
        ))

        # 不存在的订单
        url = reverse('transaction-detail', kwargs=dict(pk=999999))
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, dict(error_code='not_found', detail='未找到。'))

        # 订单非商户所有
        account = self.factory.create_account()
        self.factory.create_merchant(account=account)
        pk = self.factory.create_transaction(account=account).id
        url = reverse('transaction-detail', kwargs=dict(pk=pk))
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

    def test_update(self):
        payment = self.factory.create_payment(note='old note')
        transaction = self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
            content_object=payment,
            account=self.account,
        )

        url = reverse('transaction-detail', kwargs=dict(pk=transaction.id))
        response = self.client.put(url, data=dict(note='new note'), Token=self.token, format='json')
        resp_json = response.json()

        self.assertEqual(resp_json['note'], 'new note')

        # 可修改备注为''
        response = self.client.put(url, data=dict(note=''), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json['note'], '')

        # 非商户收款订单或退款订单
        transaction.transaction_type = TRANSACTION_TYPE['MERCHANT_SHARE']
        transaction.save()
        url = reverse('transaction-detail', kwargs=dict(pk=transaction.id))
        response = self.client.put(url, data=dict(note='new note'), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

        # 非商户
        payment = self.factory.create_payment(note='old note')
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
            content_object=payment,
        )
        response = self.client.put(url, data=dict(note='new note'), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

        # 订单非商户所有
        account = self.factory.create_account()
        self.factory.create_merchant(account=account)
        pk = self.factory.create_transaction(
            account=account, transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE']).id

        url = reverse('transaction-detail', kwargs=dict(pk=pk))
        response = self.client.put(url, data=dict(note='new note'), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})

    def test_refund(self):
        payment = self.factory.create_payment(status=PAYMENT_STATUS['FINISHED'])
        transaction = self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
            content_object=payment,
            account=self.account,
        )

        url = reverse('transaction-refund', kwargs=dict(pk=transaction.id))
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.not_frozen_payment)

        # payment not exist
        url = reverse('transaction-refund', kwargs=dict(pk='wrong_id'))
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, {'detail': '未找到。', 'error_code': 'not_found'})
