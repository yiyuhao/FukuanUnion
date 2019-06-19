#
#      File: merchant.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import re
from functools import wraps
from uuid import uuid4

import requests_mock

from common.doclink.config import WechatHttpApiConfig
from test.unittest.fake_factory.fake_factory import fake


def mock_wechat_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with requests_mock.Mocker() as m:
            pattern = re.compile(fr'^{WechatHttpApiConfig.base_url}{WechatHttpApiConfig.code_to_session}.*')
            m.register_uri('GET', pattern, json=WechatLoginCallback(unionid=kwargs.get('unionid')).mock_success)
            result = f(*args, **kwargs)
        return result
    return wrapper


class WechatLoginCallback:
    """
    errcode 的合法值
        -1	系统繁忙，此时请开发者稍候再试
        0	请求成功
        40029	code 无效
        45011	频率限制，每个用户每分钟100次
    """

    def __init__(self, unionid=None, openid=None, validate=None):
        self.openid = openid or f'mock_{uuid4().hex}'
        self.unionid = unionid or f'mock_{uuid4().hex}'
        self.validate = validate

    def mock_success(self, request=None, context=None):
        if self.validate:
            assert self.validate(request)
        return dict(
            openid=self.openid,
            session_key='session_key',
            unionid=self.unionid
        )


class WechatGetAccessToken(object):
    url_pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/oauth2/access_token\?[\w\W]*')
    
    def __init__(self, access_token=None, openid=None, validate=None):
        self.openid = openid or f'mock_openid_{uuid4().hex}'
        self.access_token = access_token or f'mock_accesstoken_{uuid4().hex}'
        self.validate = validate
    
    def mock_success(self, request=None, context=None):
        if self.validate:
            assert self.validate(request)
        return dict(
            access_token=self.access_token,
            expires_in=7200,
            refresh_token=f'refresh_token_{str(uuid4())}',
            openid=self.openid,
            scope='SCOPE',
        )


class WechatGetUserInfoCallback(object):
    
    url_pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/userinfo\?[\w\W]*')
    
    def __init__(self, validate=None, user_info=None):
        self.validate = validate
        self.user_info = user_info
    
    def mock_success(self, request=None, context=None):
        if self.validate:
            assert self.validate(request)
        if self.user_info:
            return self.user_info
        
        rep_json = dict(
            openid=str(uuid4()),
            nickname=fake.name(),
            sex=1,
            province='province',
            city='province',
            country='country',
            headimgurl='http://t2.hddhhn.com/uploads/tu/201610/198/hkgip2b102z.jpg',
            privilege=["PRIVILEGE1" "PRIVILEGE2"],
            unionid=str(uuid4()),
        )
        return rep_json

