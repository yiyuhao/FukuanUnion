# -*- coding: utf-8 -*-

from puser.core import client
from common.token_store import TokenStore
from common.weixin_login import WeixinSession


class MockClient:
    def __init__(self, openid, unionid):
        self.openid = openid
        self.unionid = unionid
        self.id = 10


class MockLoginFlow:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.weixin_session = WeixinSession('openid', 'session_key')

    def jscode2session(self, code):
        pass

    def session2token(self, token_session):
        token_session['weixin_session'] = self.weixin_session
        token_session.create_token()


class MockDbManager:
    def get_or_create_client_with_weixin_id(openid, unionid):
        return MockClient(openid, unionid)


class TestUseCase:
    def test_login(self):
        token_session = TokenStore(namespace='client')
        result = client.UseCase.wechat_login('code', token_session, MockLoginFlow, MockDbManager)
        assert token_session['client_id'] == 10
        assert token_session['weixin_session'].data == {
            'openid': 'openid', 'session_key': 'session_key', 'unionid': None}
        assert result is not None and result['token'] == token_session.token
