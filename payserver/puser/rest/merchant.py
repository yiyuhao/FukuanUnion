# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.error_handler import raise_with_code
from common.models import Merchant, PaymentQRCode
from puser import error_codes
from puser.core import auth
from puser.exceptions import DataNotFound


class GetMerchantInfoRequestSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ('id', 'name', 'description', 'avatar_url', 'status')
        read_only_fields = ('id', 'name', 'description', 'avatar_url', 'status')

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class GetMerchantInfo(auth.BasicTokenAuthMixin, APIView):

    def get(self, request):
        input_serializer = GetMerchantInfoRequestSerializer(data=request._request.GET)
        input_serializer.is_valid(raise_exception=True)

        uuid = input_serializer.validated_data['uuid']
        try:
            qr_code = PaymentQRCode.objects.prefetch_related('merchant').get(uuid=uuid)
            merchant = qr_code.merchant
        except PaymentQRCode.DoesNotExist:
            raise raise_with_code(DataNotFound(), error_codes.payment_uuid_not_found)
        except Exception:  # TODO catch specific exception
            raise raise_with_code(DataNotFound(), error_codes.no_merchant_bind_with_uuid)

        output_serializer = MerchantSerializer(merchant)
        return Response(output_serializer.data)
