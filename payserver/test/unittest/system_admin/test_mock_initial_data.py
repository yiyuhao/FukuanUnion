# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from common.models import *
from padmin.query_manage.financial_query import FinancialQuery

from django.test import TestCase

class TestRefundManager(TestCase):

   def test_mock(self):
       from .create_data import CreateData

       CreateData.initial_base_date()
       sharing_details = CreateData.initial_mock_data()
       data = FinancialQuery.data_overview()
       self.assertEqual(data['merchant'], 4)
       self.assertEqual(data['inviter'], 3)
       self.assertEqual(data['client'], 6)
       self.assertEqual(data['coupon'], 18)
       self.assertEqual(data['coupon_used'], 16)
       self.assertEqual(data['payment']['wechat'], 271.92)
       self.assertEqual(data['payment']['alipay'], 344.33)
       self.assertEqual(data['payment']['total'], 616.25)

       data = FinancialQuery.transaction_details()
       self.assertEqual(data['result']['all_order_price'], 697.55)
       self.assertEqual(data['result']['all_paid_price'], 616.25)
       self.assertEqual(data['result']['all_paid_price_wechat'], 271.92)
       self.assertEqual(data['result']['all_paid_price_alipay'], 344.33)
       self.assertEqual(data['result']['all_ordinary'], 158.05)
       self.assertEqual(data['result']['all_ordinary_alipay'], 97.35)
       self.assertEqual(data['result']['all_ordinary_wechat'], 60.7)
       self.assertEqual(data['result']['all_preferential'], 458.2)
       self.assertEqual(data['result']['all_preferential_alipay'], 246.98)
       self.assertEqual(data['result']['all_preferential_wechat'], 211.22)
       self.assertEqual(len(data['data']), 7)

       data = FinancialQuery.sharing_details()
       self.assertEqual(data['result']['all_paid_price'], 458.2)
       self.assertEqual(data['result']['all_share_all'], sharing_details['all_share_all'])
       self.assertEqual(data['result']['all_share_platform'], sharing_details['all_share_platform'])
       self.assertEqual(data['result']['all_share_inviter'], sharing_details['all_share_inviter'])
       self.assertEqual(data['result']['all_share_originator'], sharing_details['all_share_originator'])
       self.assertEqual(len(data['data']), 6)

       data = FinancialQuery.withdraw_record()
       self.assertEqual(data['result']['with_draw_records'], 7)
       self.assertEqual(data['result']['with_draw_total_money'], 40.3)
       self.assertEqual(len(data['data']), data['result']['with_draw_records'])

