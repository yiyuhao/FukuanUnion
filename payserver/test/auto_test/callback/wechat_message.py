# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import re
import random

from test.auto_test.callback.base import BaseCallback, call_validate

WX_ERROR_RESPONSE = {
    "INVALID_APP_ID": {"errcode": 40013, "errmsg": "invalid appid"},
    "INVALID_APP_SECRET": {"errcode": 40001, "errmsg": "invalid appSecret"},
    "INVALID_GRANT_TYPE": {"errcode": 40002, "errmsg": "invalid grant_type"},
    "IP_NOT_IN_WHITE_LIST": {"errcode": 40164, "errmsg": "ip not in white list"},
}


class WechatPushMessageCallback(BaseCallback):
    url_pattern = re.compile(r'^https://api\.weixin\.qq\.com/cgi-bin/message/template/send\?access_token=[\w\W]*')
    
    def __init__(self, custom_response=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_response = custom_response
        
    def set_custom_response(self, custom_response):
        self.custom_response = custom_response
    
    @call_validate
    def mock_success(self, request=None, context=None):
        return self.custom_response or {
           "errcode": 0,
           "errmsg": "ok",
           "msgid": random.random()
       }
    
    @call_validate
    def mock_invalid_access_token(self, request=None, context=None):
        return self.custom_response or {
            "errcode": 40001,
            "errmsg": "invalid credential, access_token is invalid or not latest hint: [AQF5HA04758886!]"
        }


class WechatRefreshToken(BaseCallback):
    url_pattern = re.compile(r'^https://api\.weixin\.qq\.com/cgi-bin/token\?grant_type=client_credential[\w\W]*')
    
    def __init__(self, custom_response=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_response = custom_response
        
    def set_custom_response(self, custom_response):
        self.custom_response = custom_response

    @call_validate
    def mock_success(self, request=None, context=None):
        return self.custom_response or {"access_token": "ACCESS_TOKEN", "expires_in": 7200}

    @call_validate
    def mock_invalid_app_id(self, request=None, context=None):
        return self.custom_response or WX_ERROR_RESPONSE['INVALID_APP_ID']

    @call_validate
    def mock_invalid_app_secret(self, request=None, context=None):
        return self.custom_response or WX_ERROR_RESPONSE['INVALID_APP_SECRET']

    @call_validate
    def mock_invalid_app_grant_type(self, request=None, context=None):
        return self.custom_response or WX_ERROR_RESPONSE['INVALID_GRANT_TYPE']

    @call_validate
    def mock_ip_not_in_white_list(self, request=None, context=None):
        return self.custom_response or WX_ERROR_RESPONSE['IP_NOT_IN_WHITE_LIST']