# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from common.auth.internal.validate_util import TokenValidate, ValidateTokenError


class InternalAuthentication(BaseAuthentication):
    """
    用于服务器与服务器之间调用的Authentication。
    注意不要用来做客户端与服务端的Authentication，因为容易导致token泄露。
    """

    def authenticate(self, request):

        time_stamp = request.data.get('timestamp', '')
        random_key = request.data.get('key', '')
        signature = request.data.get('signature', '')
        key_type = request.data.get('key_type', '')
        data = {
            'timestamp': time_stamp,
            'key': random_key,
            'signature': signature,
            'key_type': key_type
        }
        try:
            validator = TokenValidate(key_type)
            validator.validate(data)
        except ValidateTokenError as e:
            raise exceptions.AuthenticationFailed()

        return None, None
