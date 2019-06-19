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
from common.payment.base import PaymentBaseUseCases
from puser import error_codes
from puser.core import auth
from puser.exceptions import DataNotFound, InvalidStatus
from puser.rest.coupon import CouponSerializer


class PaymentPollResultRequestSerializer(serializers.Serializer):
    payment_serial_number = serializers.CharField()
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)
    accuracy = serializers.FloatField(allow_null=True)

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def create(self, validated_data):
        raise NotImplementedError()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('serial_number', 'datetime', 'status', 'order_price')

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def create(self, validated_data):
        raise NotImplementedError()


class PaymentResultSerializer(serializers.Serializer):
    payment = PaymentSerializer(read_only=True)
    coupons = CouponSerializer(read_only=True, many=True)

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def create(self, validated_data):
        raise NotImplementedError()


class PaymentPollResultView(auth.BasicTokenAuthMixin, APIView):
    def post(self, request):
        input_serializer = PaymentPollResultRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        payment_serial_number = input_serializer.validated_data['payment_serial_number']
        try:
            payment = Payment.objects.get(serial_number=payment_serial_number)
        except Payment.DoesNotExist:
            raise raise_with_code(DataNotFound(), error_codes.payment_not_found)

        if payment.client_id != request.user.id:
            raise raise_with_code(DataNotFound(), error_codes.payment_not_found)

        if payment.status == config.PAYMENT_STATUS.UNPAID:
            return Response({
                'payment': {
                    'status': config.PAYMENT_STATUS.UNPAID
                }
            })

        if payment.status != config.PAYMENT_STATUS.FROZEN:
            raise raise_with_code(InvalidStatus(), error_codes.invalid_payment_status)

        longitude = input_serializer.validated_data.get('longitude', None)
        latitude = input_serializer.validated_data.get('latitude', None)
        accuracy = input_serializer.validated_data.get('accuracy', None)

        coupons = PaymentBaseUseCases.grant_coupons(payment, longitude, latitude, accuracy)

        output_serializer = PaymentResultSerializer(dict(payment=payment, coupons=coupons))
        return Response(output_serializer.data)
