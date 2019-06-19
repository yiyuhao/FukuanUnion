# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from dynaconf import settings as dynasettings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.model_manager.payment_manager import PaymentManager
from common.model_manager.refund_manager import RefundManager
from common.models import Payment, Refund
from common.payment.alipay import AlipayUseCases
from common.payment.exceptions import InvalidStatusError
from common.payment.wechat import WechatPaymentUseCases
from merchant.utils import send_pay_success_wechat_message, send_voice_message_to_merchant_app

logger = logging.getLogger(__name__)


class WechatPaymentCallbackView(APIView):
    payment_use_case_cls = WechatPaymentUseCases
    appid = dynasettings.CLIENT_MINI_APP_ID
    mch_id = dynasettings.WECHAT_MERCHANT_ID

    response_template = '<xml><return_code><![CDATA[{}]]></return_code>'
    '<return_msg><![CDATA[{}]]></return_msg></xml>'

    def post(self, request):
        body = request.body
        use_cases = self.payment_use_case_cls()
        callback_msg = use_cases.api_cls.parse_xml_message(body)
        sign_type = callback_msg.pop('sign_type', 'MD5')
        sign = callback_msg.pop('sign', None)

        use_cases.api_instance_without_cert.sign_message(callback_msg, sign_type)
        expected_sign = callback_msg['sign']

        # verify the sign
        if sign != expected_sign:
            return Response(data=self.response_template.format('FAIL', '签名失败'),
                            headers={'Content-Type': 'text/xml'})

        # check the error code
        if callback_msg['return_code'] != 'SUCCESS' or callback_msg['result_code'] != 'SUCCESS':
            return Response(data=self.response_template.format('FAIL', '参数错误'),
                            headers={'Content-Type': 'text/xml'})

        if callback_msg['appid'] != self.appid \
                or callback_msg['mch_id'] != str(self.mch_id):
            return Response(data=self.response_template.format('FAIL', '参数错误'),
                            headers={'Content-Type': 'text/xml'})

        # get the payment from DB
        try:
            payment = Payment.objects.get(serial_number=callback_msg['out_trade_no'])
        except Payment.DoesNotExist:
            return Response(data=self.response_template.format('FAIL', '参数错误'),
                            headers={'Content-Type': 'text/xml'})

        paid_price = payment.order_price - payment.coupon.discount \
            if payment.coupon else payment.order_price

        # check the price
        if paid_price != int(callback_msg['total_fee']):
            return Response(data=self.response_template.format('FAIL', '参数错误'),
                            headers={'Content-Type': 'text/xml'})

        try:
            use_cases.on_payment_success(payment)
        except InvalidStatusError:
            logger.info('wechat payment duplicate callback')
        else:
            # send wechat and voice message to merchant
            payment.refresh_from_db()
            send_pay_success_wechat_message(payment)
            send_voice_message_to_merchant_app(payment)

        return Response(data=self.response_template.format('SUCCESS', 'OK'),
                        headers={'Content-Type': 'text/xml'})


class AlipayPaymentCallbackView(APIView):
    payment_use_case_cls = AlipayUseCases

    def post(self, request):
        use_cases = self.payment_use_case_cls()
        callback_msg = dict(request.POST)
        for k in callback_msg.keys():
            if type(callback_msg[k]) is list:
                callback_msg[k] = callback_msg[k][0] if callback_msg[k] else ''
        sign = callback_msg.pop('sign')
        callback_msg.pop('sign_type')
        verify_sign_pass = use_cases.api_instance.verify_sign_of_async_msg(callback_msg, sign)

        # Check the sign
        if not verify_sign_pass:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Sign Error')

        # Check the parameters
        if callback_msg['trade_status'] not in ('TRADE_SUCCESS', 'TRADE_FINISHED'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Status Error')

        # get the payment from DB
        try:
            payment = Payment.objects.get(serial_number=callback_msg['out_trade_no'])
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='out_trade_no Error')

        use_cases.on_payment_success(payment)

        # send wechat and voice message to merchant
        payment.refresh_from_db()
        send_pay_success_wechat_message(payment)
        send_voice_message_to_merchant_app(payment)

        return Response(status=status.HTTP_200_OK, data='OK')


class WechatRefundCallbackView(APIView):
    payment_use_case_cls = WechatPaymentUseCases
    appid = dynasettings.CLIENT_MINI_APP_ID
    mch_id = dynasettings.WECHAT_MERCHANT_ID

    response_template = '<xml><return_code><![CDATA[{}]]></return_code>'
    '<return_msg><![CDATA[{}]]></return_msg></xml>'

    def post(self, request):
        body = request.body
        use_cases = self.payment_use_case_cls()
        callback_msg = use_cases.api_cls.parse_xml_message(body)

        # check the error code
        if callback_msg['return_code'] != 'SUCCESS':
            return Response(data=self.response_template.format('FAIL', '参数错误'))

        if callback_msg['appid'] != self.appid \
                or callback_msg['mch_id'] != str(self.mch_id):
            return Response(data=self.response_template.format('FAIL', '参数错误'))

        encrypt_data = callback_msg['req_info']
        decrypt_data = use_cases.api_cls.parse_xml_message(
            use_cases.api_instance_without_cert.decrypt_data(encrypt_data))

        # get the payment from DB
        try:
            refund = Refund.objects.get(serial_number=decrypt_data['out_refund_no'])
        except Refund.DoesNotExist:
            return Response(data=self.response_template.format('FAIL', '参数错误'))

        if decrypt_data['refund_status'] != 'SUCCESS':
            use_cases.on_refund_fail(refund)

            # send wechat message to merchant
            refund_manager = RefundManager(refund)
            refund_manager.send_refund_fail_message()

            return Response(data=self.response_template.format('SUCCESS', 'OK'))

        payment = refund.payment
        paid_price = payment.order_price - payment.coupon.discount \
            if payment.coupon else payment.order_price

        # check the price
        if paid_price != int(decrypt_data['refund_fee']):
            return Response(data=self.response_template.format('FAIL', '参数错误'))

        use_cases.on_refund_success(refund)

        # send wechat message to merchant
        refund_manager = RefundManager(refund)
        refund_manager.send_refund_success_message()

        return Response(data=self.response_template.format('SUCCESS', 'OK'))
