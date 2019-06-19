# -*- coding: utf-8 -*-

import pytest
from doclink.exceptions import StatusCodeUnexpectedError

from common.weixin_login import WeixinSession, LoginFlow, LoginError
from common.token_store import TokenStore


def test_weixin_session():
    ws = WeixinSession('openid', 'session_key', 'unionid')
    assert ws == ws.data == {'openid': 'openid', 'session_key': 'session_key', 'unionid': 'unionid'}


class MockConsumerSuccessed:
    def jscode2session(appid, secret, js_code):
        return {'openid': 'openid', 'session_key': 'session_key', 'unionid': 'unionid'}


class MockConsumerErrorStatusCode:
    def jscode2session(appid, secret, js_code):
        raise StatusCodeUnexpectedError(200, 500, None)


class MockConsumerErrorResp:
    def jscode2session(appid, secret, js_code):
        return {'errcode': 12}


class TestLoginFlow:
    def test_jscode2session_successed(self):
        login_flow = LoginFlow('appid', 'app_secret')
        login_flow.jscode2session('code', consumer=MockConsumerSuccessed)

        assert login_flow.weixin_session == {
            'openid': 'openid',
            'session_key': 'session_key',
            'unionid': 'unionid'}

    def test_jscode2session_with_status_code_error(self):
        login_flow = LoginFlow('appid', 'app_secret')
        with pytest.raises(LoginError):
            login_flow.jscode2session('code', consumer=MockConsumerErrorStatusCode)

    def test_jscode2session_with_error_resp(self):
        login_flow = LoginFlow('appid', 'app_secret')
        with pytest.raises(LoginError):
            login_flow.jscode2session('code', consumer=MockConsumerErrorResp)

    def test_session2token(self):
        token_session = TokenStore()
        login_flow = LoginFlow('appid', 'app_secret')
        login_flow.jscode2session('code', consumer=MockConsumerSuccessed)
        login_flow.save(token_session)

        assert token_session.token is not None
        assert token_session['weixin_session'] == login_flow.weixin_session
        assert not token_session.modified
        assert token_session.accessed
