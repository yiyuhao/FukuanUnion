# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from collections import UserDict
import logging

from common.doclink import weixin_auth_consumer
from doclink.exceptions import StatusCodeUnexpectedError


logger = logging.getLogger(__name__)


class LoginError(Exception):
    def __init__(self, msg='login failed'):
        super().__init__(msg)


class WeixinSession(UserDict):
    """docstring for WeixinSession"""

    def __init__(self, openid, session_key, unionid=None):
        self.openid = openid
        self.session_key = session_key
        self.unionid = unionid
        super().__init__(openid=openid, session_key=session_key, unionid=unionid)


class LoginFlow:
    def __init__(self, appid, app_secret):
        self.appid = appid
        self.app_secret = app_secret
        self.weixin_session = None

    def jscode2session(self, code, consumer=weixin_auth_consumer):
        """Step 1, exchange weixin session from code"""
        try:
            resp_json = consumer.jscode2session(
                appid=self.appid,
                secret=self.app_secret,
                js_code=code)
            if 'errcode' in resp_json:
                logger.error(f'jscode2session failed\n {resp_json}')
                raise LoginError(str(resp_json))
        except StatusCodeUnexpectedError as e:
            raise LoginError(f'status code error: {e.status_code}')
        else:
            self.weixin_session = WeixinSession(**resp_json)

    def save(self, token_session, **extra):
        assert self.weixin_session is not None

        # We must set session attr before create_token, else
        # token will be set to none.
        token_session['weixin_session'] = self.weixin_session

        for k, v in extra.items():
            token_session[k] = v

        token_session.create_token()
