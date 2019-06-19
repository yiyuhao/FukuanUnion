# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import re
import uuid

import requests_mock
from django.utils import timezone
from rest_framework.reverse import reverse

from common.auth.internal.validate_util import TokenGenerate
from common.payment.wechat import WechatPaymentUseCases
from puser.tasks import wechat_refund_status_sync
from test.auto_test.callback.wechat_pay import WechatPayCallback
from test.auto_test.steps.base import BaseStep


class WechatPaySteps(BaseStep):
    def __init__(self, client_token, app_id, mch_id):
        super().__init__()
        self.client_token = client_token
        self.app_id = app_id
        self.mch_id = mch_id

    @staticmethod
    def validate(request):
        return True

    def place_order(self, merchant_id, order_price, coupon_id):
        pattern = re.compile(r'^https://api\.mch\.weixin\.qq\.com/pay/unifiedorder$')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern,
                           text=WechatPayCallback(self.app_id, self.mch_id,
                                                  self.validate).mock_place_order_success)
            url = reverse('place_order')
            self.client.credentials(HTTP_ACCESS_TOKEN=self.client_token)
            resp = self.client.post(url,
                                    data={"merchant_id": merchant_id,
                                          'order_price': order_price,
                                          'coupon_id': coupon_id,
                                          'channel': 0},
                                    format='json')
            return resp.json()

    def payment_callback(self, app_id, mch_id, openid, payment_serial_number, total_fee):
        params = dict(
            appid=app_id,
            bank_type='CFT',
            cash_fee=str(total_fee),
            fee_type='CNY',
            is_subscribe='N',
            mch_id=mch_id,
            nonce_str=uuid.uuid4().hex,
            openid=openid,
            out_trade_no=payment_serial_number,
            result_code='SUCCESS',
            return_code='SUCCESS',
            time_end=timezone.now().strftime('%Y%m%d%H%M%S'),
            total_fee=total_fee,
            trade_type='JSAPI',
            transaction_id=uuid.uuid4().hex
        )

        usecases = WechatPaymentUseCases()
        usecases.api_instance_without_cert.sign_message(params)
        xml = usecases.api_instance_without_cert.build_xml_message(params)

        url = reverse('wechat_payment_callback')
        resp = self.client.post(url, xml, content_type='text/xml')
        return resp

    def cancel_order(self, payment_serial_number):
        pattern = re.compile(r'^https://api\.mch\.weixin\.qq\.com/pay/closeorder$')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern,
                           text=WechatPayCallback(self.app_id, self.mch_id,
                                                  self.validate).mock_cancel_order_success)
            url = reverse('cancel_order')
            self.client.credentials(HTTP_ACCESS_TOKEN=self.client_token)
            resp = self.client.post(url,
                                    data={"payment_serial_number": payment_serial_number,
                                          'pay_channel': 0},
                                    format='json')
            return resp.json()

    def refund_callback(self, app_id, mch_id, payment_serial_number, refund_serial_number, amount):
        usecases = WechatPaymentUseCases()
        encrypt_data = f"""<root>
<out_refund_no><![CDATA[{refund_serial_number}]]></out_refund_no>
<out_trade_no><![CDATA[{payment_serial_number}]]></out_trade_no>
<refund_account><![CDATA[REFUND_SOURCE_RECHARGE_FUNDS]]></refund_account>
<refund_fee><![CDATA[{amount}]]></refund_fee>
<refund_id><![CDATA[50000008402018100906610349654]]></refund_id>
<refund_recv_accout><![CDATA[支付用户零钱]]></refund_recv_accout>
<refund_request_source><![CDATA[API]]></refund_request_source>
<refund_status><![CDATA[SUCCESS]]></refund_status>
<settlement_refund_fee><![CDATA[{amount}]]></settlement_refund_fee>
<settlement_total_fee><![CDATA[{amount}]]></settlement_total_fee>
<success_time><![CDATA[2018-10-09 15:03:04]]></success_time>
<total_fee><![CDATA[{amount}]]></total_fee>
<transaction_id><![CDATA[4200000178201810090180106008]]></transaction_id>
</root>"""
        req_info = usecases.api_instance_without_cert.encrypt_data(encrypt_data)
        params = dict(
            appid=app_id,
            mch_id=mch_id,
            nonce_str=uuid.uuid4().hex,
            return_code='SUCCESS',
            req_info=req_info
        )

        usecases.api_instance_without_cert.sign_message(params)
        xml = usecases.api_instance_without_cert.build_xml_message(params)

        url = reverse('wechat_refund_callback')
        resp = self.client.post(url, xml, content_type='text/xml')
        return resp

    def refund_status_sync(self):
        url = reverse('refund_status_sync')
        self.client.credentials(HTTP_ACCESS_TOKEN=self.client_token)
        data = TokenGenerate('TXLcqm9eMxH5agyHnXmLFappbDfzYy4u',
                             'refresh_token').get_token_params()
        resp = self.client.post(url,
                                data=data,
                                format='json')
        return resp.json()

    def call_task_refund_status_sync(self, refund_serial_number):
        pattern = re.compile(r'^https://api\.mch\.weixin\.qq\.com/pay/refundquery$')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern,
                           text=WechatPayCallback(self.app_id, self.mch_id,
                                                  self.validate).mock_refund_query_success)
            wechat_refund_status_sync(refund_serial_number)
