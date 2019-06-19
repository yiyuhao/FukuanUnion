# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from common.models import *
from padmin.query_manage.settlement_query import SettlementUseCase, SettlementQuery
from padmin.exceptions import SettlementDuplicateException, SettlementAbnormalBalanceException
from test.unittest.fake_factory import PayunionFactory


class TestSettlement(TestCase):
    
    def prepare_data(self):
        from .base_data import create_base_data
        create_base_data()
        fake_factory = PayunionFactory()
        curr_time = timezone.now()
        yesterday = curr_time - timedelta(days=1)

        client = fake_factory.create_client(status=SYSTEM_USER_STATUS['USING'])
        inviter = fake_factory.create_marketer(inviter_type=MARKETER_TYPES['SALESMAN'],
                                               status=SYSTEM_USER_STATUS['USING'])
        merchant = fake_factory.create_merchant(status=MERCHANT_STATUS['USING'], inviter=inviter)
        merchant.type = MERCHANT_TYPE['ENTERPRISE']
        merchant.save()
        
        pay_money = 10 * 100
        payment = Payment.objects.create(
            serial_number="20181102172102347024194949482317",
            datetime=yesterday,
            pay_channel=PAY_CHANNELS['WECHAT'],
            status=PAYMENT_STATUS['FINISHED'],
            merchant=merchant,
            client=client,
            order_price=pay_money,
            coupon=None,
            coupon_granted=True,
            platform_share=0,
            inviter_share=0,
            originator_share=0,
        )
        merchant.account.balance = pay_money
        merchant.account.withdrawable_balance = pay_money

        pay_money = 5 * 100
        payment = Payment.objects.create(
            serial_number="20181102172106671737943971236656",
            datetime=yesterday,
            pay_channel=PAY_CHANNELS['ALIPAY'],
            status=PAYMENT_STATUS['FINISHED'],
            merchant=merchant,
            client=client,
            order_price=5 * 100,
            coupon=None,
            coupon_granted=True,
            platform_share=0,
            inviter_share=0,
            originator_share=0,
        )

        merchant.account.alipay_balance = pay_money
        merchant.account.alipay_withdrawable_balance = pay_money
        merchant.account.save()
    
        return merchant
    
    def test_settlement_use_case(self):
        merchant = self.prepare_data()
        bill_list = SettlementQuery.query_enterprise_merchant_pure_profit_by_day()
        self.assertEqual([{'merchant': merchant.id, 'total_wechat': 1000, 'total_alipay': 500}], bill_list)
        
        # 余额不足结算
        originator_alipay_balance = merchant.account.alipay_balance
        merchant.account.alipay_balance = originator_alipay_balance - 5
        merchant.account.save()
        for bill in bill_list:
            try:
                SettlementUseCase.settlement(bill['merchant'], bill['total_wechat'], bill['total_alipay'])
            except Exception as e:
                if isinstance(e, SettlementAbnormalBalanceException):
                    pass
                else:
                    raise Exception('Expect to appear "abnormal balance settlement exception" but not')
           
            
        # 正常结算
        merchant.account.alipay_balance = originator_alipay_balance
        merchant.account.save()
        for bill in bill_list:
            SettlementUseCase.settlement(bill['merchant'], bill['total_wechat'], bill['total_alipay'])
        self.assertEqual(len(Settlement.objects.all()), 1)
        self.assertEqual(Settlement.objects.all()[0].alipay_amount, 500)
        self.assertEqual(Settlement.objects.all()[0].wechat_amount, 1000)
        self.assertEqual(Settlement.objects.all()[0].status, SETTLEMENT_STATUS['PROCESSING'])
    
        # 重复结算
        for bill in bill_list:
            try:
                SettlementUseCase.settlement(bill['merchant'], bill['total_wechat'], bill['total_alipay'])
            except Exception as e:
                if isinstance(e, SettlementDuplicateException):
                    pass
                else:
                    raise Exception('Expect to appear "duplicate settlement exception" but not')

