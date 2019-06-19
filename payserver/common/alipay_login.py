# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from collections import UserDict


class LoginError(Exception):
    def __init__(self, msg='login failed'):
        super().__init__(msg)


class AlipaySession(UserDict):
    """docstring for AlipaySession"""

    def __init__(self, user_id, access_token, expires_in, refresh_token, re_expires_in):
        self.user_id = user_id
        self.access_token = access_token
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self.re_expires_in = re_expires_in
        super().__init__(user_id=user_id, access_token=access_token, expires_in=expires_in,
                         refresh_token=refresh_token, re_expires_in=re_expires_in)
