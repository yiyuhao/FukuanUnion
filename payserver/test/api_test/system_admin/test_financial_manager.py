# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class FinancialManagerTests(AdminSystemTestBase):

    @classmethod
    def setUpTestData(cls):
        from test.unittest.system_admin.create_data import CreateData
        CreateData.initial_base_date()
        cls.sharing_details = CreateData.initial_mock_data()

    def test_get_overview_data(self):
        """ 获取数据总览 """

        self.set_login_status(is_super=True)
        url = "/api/admin/financial/data_overview/"
        resp = self.client.get(url)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['merchant'], 4)
        self.assertEqual(resp_json['inviter'], 3)
        self.assertEqual(resp_json['client'], 6)
        self.assertEqual(resp_json['coupon'], 18)
        self.assertEqual(resp_json['coupon_used'], 16)
        self.assertEqual(resp_json['payment']['wechat'], 271.92)
        self.assertEqual(resp_json['payment']['alipay'], 344.33)
        self.assertEqual(resp_json['payment']['total'], 616.25)


    def test_get_transaction_details(self):
        """ 获取交易明细 """

        self.set_login_status(is_super=True)
        url = "/api/admin/financial/transaction_details/"
        resp = self.client.get(url)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['result']['all_order_price'], 697.55)
        self.assertEqual(resp_json['result']['all_paid_price'], 616.25)
        self.assertEqual(resp_json['result']['all_paid_price_wechat'], 271.92)
        self.assertEqual(resp_json['result']['all_paid_price_alipay'], 344.33)
        self.assertEqual(resp_json['result']['all_ordinary'], 158.05)
        self.assertEqual(resp_json['result']['all_ordinary_alipay'], 97.35)
        self.assertEqual(resp_json['result']['all_ordinary_wechat'], 60.7)
        self.assertEqual(resp_json['result']['all_preferential'], 458.2)
        self.assertEqual(resp_json['result']['all_preferential_alipay'], 246.98)
        self.assertEqual(resp_json['result']['all_preferential_wechat'], 211.22)
        self.assertEqual(len(resp_json['data']), 7)

    def test_get_sharing_details(self):
        """ 获取分成明细 """

        self.set_login_status(is_super=True)
        url = "/api/admin/financial/sharing_details/"
        resp = self.client.get(url)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['result']['all_paid_price'], 458.2)
        self.assertEqual(resp_json['result']['all_share_all'], self.sharing_details['all_share_all'])
        self.assertEqual(resp_json['result']['all_share_platform'], self.sharing_details['all_share_platform'])
        self.assertEqual(resp_json['result']['all_share_inviter'], self.sharing_details['all_share_inviter'])
        self.assertEqual(resp_json['result']['all_share_originator'], self.sharing_details['all_share_originator'])
        self.assertEqual(len(resp_json['data']), 6)

    def test_get_withdraw_record(self):
        """ 获取提现明细 """

        self.set_login_status(is_super=True)
        url = "/api/admin/financial/withdraw_record/"
        resp = self.client.get(url)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['result']['with_draw_records'], 7)
        self.assertEqual(resp_json['result']['with_draw_total_money'], 40.3)
        self.assertEqual(len(resp_json['data']), resp_json['result']['with_draw_records'])

    def test_download__csv(self):
        """下载csv文件"""

        from datetime import timedelta
        from django.utils import timezone
        from urllib.parse import quote

        curr_time = timezone.now()
        start_time = curr_time - timedelta(days=10)
        curr_time = curr_time.strftime('%Y-%m-%d')
        start_time = start_time.strftime('%Y-%m-%d')

        self.set_login_status(is_super=True)
        url = f"/api/admin/financial/transaction_details/?start_date={start_time}&end_date={curr_time}&type=csv"
        name = f"""attachment; filename*=utf-8''{quote("资金账单")}.csv"""
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["content-type"], 'text/csv')
        self.assertEqual(resp["content-disposition"], name)

        url = f'/api/admin/financial/sharing_details/?start_date={start_time}&end_date={curr_time}&type=csv'
        name = f"""attachment; filename*=utf-8''{quote("资金分成")}.csv"""
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["content-type"], 'text/csv')
        self.assertEqual(resp["content-disposition"], name)

        url = f"/api/admin/financial/withdraw_record/?start_date={start_time}&end_date={curr_time}&type=csv"
        name = f"""attachment; filename*=utf-8''{quote("提现申请记录表")}.csv"""
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["content-type"], 'text/csv')
        self.assertEqual(resp["content-disposition"], name)