# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from faker import Faker

from common.doclink.wechat_pay_apis import WechatPayApis
from common.models import Refund
from test.auto_test.callback.base import BaseCallback, call_validate

fake = Faker('zh_CN')


class WechatPayCallback(BaseCallback):
    def __init__(self, appid, mch_id, validate=None):
        super().__init__(validate)
        self.appid = appid
        self.mch_id = mch_id

    @call_validate
    def mock_place_order_success(self, request=None, context=None):
        return f"""<xml><return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[OK]]></return_msg>
<appid><![CDATA[{self.appid}]]></appid>
<mch_id><![CDATA[{self.mch_id}]]></mch_id>
<nonce_str><![CDATA[{fake.pystr(min_chars=16, max_chars=16)}]]></nonce_str>
<sign><![CDATA[{fake.pystr(min_chars=32, max_chars=32)}]]></sign>
<result_code><![CDATA[SUCCESS]]></result_code>
<prepay_id><![CDATA[wx{fake.pystr(min_chars=34, max_chars=34)}]]></prepay_id>
<trade_type><![CDATA[JSAPI]]></trade_type>
</xml>"""

    @call_validate
    def mock_cancel_order_success(self, request=None, context=None):
        return f"""<xml><return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[OK]]></return_msg>
<appid><![CDATA[{self.appid}]]></appid>
<mch_id><![CDATA[{self.mch_id}]]></mch_id>
<sub_mch_id><![CDATA[]]></sub_mch_id>
<nonce_str><![CDATA[{fake.pystr(min_chars=16, max_chars=16)}]]></nonce_str>
<sign><![CDATA[{fake.pystr(min_chars=32, max_chars=32)}]]></sign>
<result_code><![CDATA[SUCCESS]]></result_code>
</xml>"""

    @call_validate
    def mock_refund_success(self, request=None, content=None):
        request_params = WechatPayApis.parse_xml_message(request.body)

        return f"""<xml><return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[OK]]></return_msg>
<appid><![CDATA[{self.appid}]]></appid>
<mch_id><![CDATA[{self.mch_id}]]></mch_id>
<nonce_str><![CDATA[{fake.pystr(min_chars=16, max_chars=16)}]]></nonce_str>
<sign><![CDATA[{fake.pystr(min_chars=32, max_chars=32)}]]></sign>
<result_code><![CDATA[SUCCESS]]></result_code>
<transaction_id><![CDATA[4200000185201810080748186130]]></transaction_id>
<out_trade_no><![CDATA[{request_params['out_trade_no']}]]></out_trade_no>
<out_refund_no><![CDATA[{request_params['out_refund_no']}]]></out_refund_no>
<refund_id><![CDATA[50000208532018100806606875740]]></refund_id>
<refund_channel><![CDATA[]]></refund_channel>
<refund_fee>{request_params['refund_fee']}</refund_fee>
<coupon_refund_fee>0</coupon_refund_fee>
<total_fee>{request_params['total_fee']}</total_fee>
<cash_fee>{request_params['total_fee']}</cash_fee>
<coupon_refund_count>0</coupon_refund_count>
<cash_refund_fee>{request_params['refund_fee']}</cash_refund_fee>
</xml>"""

    @call_validate
    def mock_refund_query_success(self, request=None, content=None):
        body = request.body
        params = WechatPayApis.parse_xml_message(body)
        refund_serial_number = params['out_refund_no']
        refund = Refund.objects.get(serial_number=refund_serial_number)
        paid_price = refund.payment.order_price - refund.payment.coupon.discount if refund.payment.coupon else refund.payment.order_price

        return f"""<xml>
<appid><![CDATA[{self.appid}]]></appid>
<cash_fee><![CDATA[100]]></cash_fee>
<mch_id><![CDATA[{self.mch_id}]]></mch_id>
<nonce_str><![CDATA[TGD85Vb9enCC6qjB]]></nonce_str>
<out_refund_no_0><![CDATA[{refund_serial_number}]]></out_refund_no_0>
<out_trade_no><![CDATA[{refund.payment.serial_number}]]></out_trade_no>
<refund_account_0><![CDATA[REFUND_SOURCE_UNSETTLED_FUNDS]]></refund_account_0>
<refund_channel_0><![CDATA[ORIGINAL]]></refund_channel_0>
<refund_count>1</refund_count>
<refund_fee>{paid_price}</refund_fee>
<refund_fee_0>{paid_price}</refund_fee_0>
<refund_id_0><![CDATA[50000208272018090706242811467]]></refund_id_0>
<refund_recv_accout_0><![CDATA[支付用户的零钱]]></refund_recv_accout_0>
<refund_status_0><![CDATA[SUCCESS]]></refund_status_0>
<refund_success_time_0><![CDATA[2018-09-07 16:10:30]]></refund_success_time_0>
<result_code><![CDATA[SUCCESS]]></result_code>
<return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[OK]]></return_msg>
<sign><![CDATA[9C608411200A16B7417894FAAD2D08A8]]></sign>
<total_fee><![CDATA[{paid_price}]]></total_fee>
<transaction_id><![CDATA[4200000174201809079044471634]]></transaction_id>
</xml>"""

    @call_validate
    def mock_withdraw_success(self, request=None, context=None):
        body = request.body
        params = WechatPayApis.parse_xml_message(body)
        partner_trade_no = params['partner_trade_no']
        nonce_str = params['nonce_str']

        return f"""<xml>
<return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[]]></return_msg>
<mch_appid><![CDATA[{self.appid}]]></mch_appid>
<mchid><![CDATA[{self.mch_id}]]></mchid>
<device_info><![CDATA[]]></device_info>
<nonce_str><![CDATA[{nonce_str}]]></nonce_str>
<result_code><![CDATA[SUCCESS]]></result_code>
<partner_trade_no><![CDATA[{partner_trade_no}]]></partner_trade_no>
<payment_no><![CDATA[1000018301201505190181489473]]></payment_no>
<payment_time><![CDATA[2015-05-19 15：26：59]]></payment_time>
</xml>"""

    @call_validate
    def mock_withdraw_faild(self, request=None, context=None):
        return f"""<xml>
<return_code><![CDATA[FAIL]]></return_code>
<return_msg><![CDATA[系统繁忙,请稍后再试.]]></return_msg>
<result_code><![CDATA[FAIL]]></result_code>
<err_code><![CDATA[SYSTEMERROR]]></err_code>
<err_code_des><![CDATA[系统繁忙,请稍后再试.]]></err_code_des>
</xml>"""