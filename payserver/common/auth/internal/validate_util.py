# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import hashlib
import time
from datetime import datetime

from common.auth.internal.const import TOKEN_CONFIG


class ValidateTokenError(Exception):
    def __init__(self, *args, **kwargs):
        super(ValidateTokenError, self).__init__(*args, **kwargs)

class TokenGenerate(object):
    """ 生成校验参数 """

    def __init__(self, token, key_type):
        self.token = token
        self.key_type = key_type

    def get_token_params(self):
        import string
        import random

        time_stamp = int(time.time())
        random_key = ''.join(random.sample(string.ascii_letters + string.digits, 32))
        key_type = self.key_type
        token = self.token

        param_list = [token, str(time_stamp), random_key, key_type]
        param_list.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(param_list).encode('utf-8'))
        signature = sha1.hexdigest()

        data = {
            'timestamp': time_stamp,
            'key': random_key,
            'signature': signature,
            'key_type': key_type
        }
        return data


class TokenValidate(object):
    """ 验证请求参数是否和合法 """

    def __init__(self, validate_type):
        self.token = TOKEN_CONFIG.get(validate_type)

    def validate(self, params):
        if self.token is None:
            raise ValidateTokenError("validate_type is invalid")

        token = self.token
        time_stamp = params['timestamp']  # 10位时间戳
        random_key = params['key']  # 随机字符串key
        key_type = params['key_type']
        signature = params['signature']


        try:
            time_stamp = int(time_stamp)
        except ValueError:
            raise ValidateTokenError("timestamp is invalid")

        # 时间合法
        current_time = datetime.utcfromtimestamp(time.time())
        request_time = datetime.utcfromtimestamp(time_stamp)
        if abs((current_time - request_time).seconds) > 120:
            raise ValidateTokenError("timestamp is invalid")

        param_list = [token, str(time_stamp), random_key, key_type]
        param_list.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(param_list).encode('utf-8'))
        hashcode = sha1.hexdigest()
        if hashcode != signature:
            raise ValidateTokenError("signature is invalid")

        return True
