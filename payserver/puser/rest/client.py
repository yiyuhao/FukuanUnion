# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

import config
from common.error_handler import raise_with_code
from common.models import Client
from common.weixin_login import LoginError
from puser import error_codes
from puser import utils
from puser.core import client, auth
from puser.exceptions import WeixinLoginUnavailable, InvalidParameter, AlipayLoginUnavailable


class ClientSerializer(serializers.ModelSerializer):
    phone_known = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ('openid_channel', 'status', 'avatar_url', 'phone_known')
        read_only_fields = ('openid_channel', 'status', 'avatar_url')

    def get_phone_known(self, obj):
        return bool(obj.phone)

    def update(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError


class LoginSerializer(serializers.Serializer):
    # input
    code = serializers.CharField(write_only=True)
    channel = serializers.ChoiceField(
        write_only=True,
        choices=config.PAY_CHANNELS.model_choices())
    # output
    access_token = serializers.CharField(read_only=True)
    client = ClientSerializer(read_only=True)


class SetPhoneSerializer(serializers.Serializer):
    # input
    iv = serializers.CharField(write_only=True)
    encrypted_data = serializers.CharField(write_only=True)
    # output
    phone_known = serializers.BooleanField(read_only=True)


class Login(auth.EmptyAllowedTokenAuthMixin, APIView):

    def post(self, request):
        # input validation
        input_serializer = LoginSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        channel = input_serializer.validated_data['channel']
        code = input_serializer.validated_data['code']

        if channel == config.PAY_CHANNELS.WECHAT:
            try:
                result = client.UseCase.wechat_login(code, request.token_session)
            except LoginError:
                raise raise_with_code(WeixinLoginUnavailable(),
                                      error_codes.service_unavailable_weixin_login)  # 503
        elif channel == config.PAY_CHANNELS.ALIPAY:
            try:
                result = client.UseCase.alipay_login(code, request.token_session)
            except LoginError:
                raise raise_with_code(AlipayLoginUnavailable(),
                                      error_codes.service_unavailable_alipay_login)  # 503
        else:
            raise raise_with_code(InvalidParameter(), error_codes.invalid_payment_channel)

        output_serializer = LoginSerializer(
            {'access_token': result['token'],
             'client': result['client']})

        return Response(output_serializer.data)


class Me(auth.BasicTokenAuthMixin, APIView):

    def get(self, request):
        output_serializer = ClientSerializer(request.user)

        return Response(output_serializer.data)


class SetPhone(auth.BasicTokenAuthMixin, APIView):

    def post(self, request):
        input_serializer = SetPhoneSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        iv = input_serializer.validated_data['iv']
        encrypted_data = input_serializer.validated_data['encrypted_data']
        session_key = request.token_session['weixin_session']['session_key']
        decrypted_data = utils.weixin_decrypt(session_key, encrypted_data, iv)

        client.UseCase.set_client_phone(request.user, decrypted_data['purePhoneNumber'])

        output_serializer = SetPhoneSerializer({'phone_known': True})

        return Response(output_serializer.data)
