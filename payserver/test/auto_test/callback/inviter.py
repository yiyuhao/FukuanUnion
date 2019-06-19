# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import json

from test.auto_test.callback.base import BaseCallback, call_validate


WX_ERRORS = {
    'INVALID_CODE': {'errcode': 40029, 'errmsg': 'invalid code'},
    'INVALID_OPENID': {"errcode": 40003, "errmsg": " invalid openid "},
    'INVALID_ACCESS_TOKEN': {"errcode": 40014, "errmsg": " invalid access_token "}
}


class SendMessageCallback(BaseCallback):
    def __init__(self, success=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__send_code = None
        self.success = success

    @call_validate
    def mock_success(self, request=None, context=None):
        return dict(
            statusCode="000000",
        )

    @call_validate
    def mock_too_frequent(self, request=None, context=None):
        return dict(
            statusCode="160038",
        )

    def mock_callback(self, request=None, context=None):
        self.__send_code = json.loads(request.text).get('datas')[0]
        if self.success:
            return self.mock_success(request, context)
        else:
            return self.mock_too_frequent(request, context)

    @property
    def get_send_code(self):
        if self.__send_code:
            return self.__send_code
        raise AttributeError('send_code haven`t generated yet, try to get it after requests')
