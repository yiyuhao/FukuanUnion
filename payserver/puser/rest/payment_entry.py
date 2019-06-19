# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from urllib.parse import quote

from django.http import HttpResponseRedirect
from rest_framework import serializers
from rest_framework.views import APIView

import config
from puser.consts import alipay_appid, alipay_api_gateway


class PaymentEntryRequestSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class PaymentEntryView(APIView):
    URL_PATTERN = '{alipay_api_gateway}/oauth2/publicAppAuthorize.htm?app_id={app_id}&scope=auth_base&redirect_uri={payweb_url}&state={uuid}'

    def get(self, request):
        input_serializer = PaymentEntryRequestSerializer(data=request._request.GET)
        input_serializer.is_valid(raise_exception=True)

        return HttpResponseRedirect(redirect_to=self.URL_PATTERN.format(
            alipay_api_gateway=alipay_api_gateway,
            app_id=alipay_appid,
            payweb_url=quote(config.VIPS['PAYWEB'] + "/pay.html"),
            uuid=input_serializer.validated_data['uuid']
        ))
