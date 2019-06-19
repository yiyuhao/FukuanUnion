# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
from datetime import timedelta

from django import db
from django.urls import reverse
from django.utils import timezone
from ipware import get_client_ip
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

import config
from common.doclink.exceptions import ApiReturnedError, ApiRequestError
from common.error_handler import raise_with_code
from common.models import Client, Merchant, Coupon
from common.payment.alipay import AlipayUseCases
from common.payment.wechat import WechatPaymentUseCases
from puser import error_codes
from puser.core import auth
from puser.exceptions import PlaceOrderError

logger = logging.getLogger(__name__)


class PlaceOrderRequestSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(write_only=True)
    merchant_id = serializers.IntegerField(write_only=True)
    order_price = serializers.IntegerField(write_only=True, min_value=1,
                                           max_value=10000000)  # 最少1分，最多10万
    coupon_id = serializers.IntegerField(write_only=True, allow_null=True)
    channel = serializers.ChoiceField(write_only=True, choices=config.PAY_CHANNELS.model_choices())

    default_error_messages = {
        'invalid_client_id': 'client is is invalid',
        'invalid_merchant_id': 'merchant id is invalid',
        'invalid_merchant_status': 'merchant status is invalid',
        'invalid_coupon_id': 'coupon id is invalid',
        'order_price_less_than_coupon_min_charge': 'order_price is less than coupon min charge',
        'invalid_coupon_status': 'invalid coupon status',
        'coupon_too_early': 'coupon cannot be used currently',
        'coupon_expired': 'coupon is expired'
    }

    def validate(self, attrs):
        try:
            client = Client.objects.get(id=attrs.get('client_id', None))
        except Client.DoesNotExist:
            raise self.fail('invalid_client_id')
        else:
            attrs['client'] = client

        try:
            merchant = Merchant.objects.get(id=attrs.get('merchant_id', None))
        except Merchant.DoesNotExist:
            raise self.fail('invalid_merchant_id')
        else:
            if merchant.status != config.MERCHANT_STATUS.USING:
                raise self.fail('invalid_merchant_status')

            attrs['merchant'] = merchant

        coupon_id = attrs.get('coupon_id', None)
        if coupon_id:
            try:
                coupon = Coupon.objects.select_related('rule').get(id=coupon_id)
            except Coupon.DoesNotExist:
                raise self.fail('invalid_coupon_id')
            else:
                attrs['coupon'] = coupon

            if coupon.client_id != client.id or coupon.rule.merchant_id != merchant.id:
                raise self.fail('invalid_coupon_id')

            if coupon.status != config.COUPON_STATUS.NOT_USED:
                raise self.fail('invalid_coupon_status')

            order_price = attrs.get('order_price', 0)
            if order_price < coupon.min_charge:
                raise self.fail('order_price_less_than_coupon_min_charge')

            now = timezone.now()
            if (coupon.rule.valid_strategy == config.VALID_STRATEGY.DATE_RANGE and
                    now.date() < coupon.rule.start_date):
                raise self.fail('coupon_too_early')

            if (coupon.rule.valid_strategy == config.VALID_STRATEGY.DATE_RANGE and
                    now.date() > coupon.rule.end_date):
                raise self.fail('coupon_expired')

            if (coupon.rule.valid_strategy == config.VALID_STRATEGY.EXPIRATION and
                    now.date() > coupon.obtain_datetime.date() + timedelta(
                        days=coupon.rule.expiration_days)):
                raise self.fail('coupon_expired')

        return attrs

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class PlaceOrder(auth.BasicTokenAuthMixin, APIView):
    alipay_usecases = AlipayUseCases
    wechat_usecases = WechatPaymentUseCases

    def post(self, request):
        input_data = dict(**request.data, client_id=request.user.id)
        input_serializer = PlaceOrderRequestSerializer(data=input_data)
        input_serializer.is_valid(raise_exception=True)

        client = input_serializer.validated_data['client']
        merchant = input_serializer.validated_data['merchant']
        order_price = input_serializer.validated_data['order_price']
        coupon = input_serializer.validated_data.get('coupon', None)
        channel = input_serializer.validated_data['channel']

        if channel == config.PAY_CHANNELS.ALIPAY:
            try:
                result = self.alipay_usecases().place_order(
                    client=client,
                    merchant=merchant,
                    coupon=coupon,
                    order_price=order_price,
                    notify_url=request.build_absolute_uri('/').strip("/") + reverse(
                        'alipay_payment_callback')
                )
            except (db.DatabaseError, ApiRequestError, ApiReturnedError) as e:
                logger.error('Placing alipay order error:{}'.format(repr(e)))
                raise raise_with_code(PlaceOrderError(),
                                      error_codes.service_error_when_placing_order)
            else:
                return Response(data=result)
        elif channel == config.PAY_CHANNELS.WECHAT:
            client_ip, _ = get_client_ip(request._request)
            try:
                result = self.wechat_usecases().place_order(
                    client=client,
                    merchant=merchant,
                    coupon=coupon,
                    order_price=order_price,
                    client_ip=client_ip,
                    notify_url=request.build_absolute_uri('/').strip("/") + reverse(
                        'wechat_payment_callback')
                )
            except (db.DatabaseError, ApiRequestError, ApiReturnedError) as e:
                logger.error('Placing wechat order error:{}'.format(repr(e)))
                raise raise_with_code(PlaceOrderError(),
                                      error_codes.service_error_when_placing_order)
            else:
                return Response(data=result)
