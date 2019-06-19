# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

import config
from common.error_handler import raise_with_code
from common.models import Payment
from common.payment.alipay import AlipayUseCases
from common.payment.wechat import WechatPaymentUseCases
from puser import error_codes
from puser.core import auth
from puser.exceptions import DataNotFound, InvalidStatus
from puser.rest.coupon import CouponSerializer


class PaymentCancelRequestSerializer(serializers.Serializer):
    payment_serial_number = serializers.CharField()
    pay_channel = serializers.ChoiceField(
        choices=config.PAY_CHANNELS.model_choices())  # 支付渠道，支付宝/微信

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def create(self, validated_data):
        raise NotImplementedError()


class PaymentCancelView(auth.BasicTokenAuthMixin, APIView):
    alipay_usecases = AlipayUseCases
    wechat_usecases = WechatPaymentUseCases

    def post(self, request):
        input_serializer = PaymentCancelRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        payment_serial_number = input_serializer.validated_data['payment_serial_number']
        try:
            payment = Payment.objects.get(serial_number=payment_serial_number)
        except Payment.DoesNotExist:
            raise raise_with_code(DataNotFound(), error_codes.payment_not_found)

        if payment.client_id != request.user.id:
            raise raise_with_code(DataNotFound(), error_codes.payment_not_found)

        if payment.status != config.PAYMENT_STATUS.UNPAID:
            raise raise_with_code(InvalidStatus(), error_codes.invalid_payment_status)

        new_coupon = None
        if input_serializer.validated_data['pay_channel'] == config.PAY_CHANNELS.WECHAT:
            new_coupon = self.wechat_usecases().cancel_order(payment)
        elif input_serializer.validated_data['pay_channel'] == config.PAY_CHANNELS.ALIPAY:
            new_coupon = self.alipay_usecases().cancel_order(payment)

        if new_coupon:
            output_serializer = CouponSerializer(new_coupon)
            return Response({'new_coupon': output_serializer.data})
        else:
            return Response({'new_coupon': None})
