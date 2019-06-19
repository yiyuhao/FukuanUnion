import uuid

from test.auto_test.callback.base import BaseCallback, call_validate

WX_ERRORS = {
    'INVALID_CODE': {'errcode': 40029, 'errmsg': 'invalid code'},
    'INVALID_OPENID': {"errcode": 40003, "errmsg": " invalid openid "},
    'INVALID_ACCESS_TOKEN': {"errcode": 40014, "errmsg": " invalid access_token "}
}


class WXCode2SessionCallback(BaseCallback):
    def __init__(self, code, mocked_openid=None, mocked_session_key=None, mocked_unionid=None,
                 *args, **kwargs):
        self.code = code
        self.mocked_openid = mocked_openid
        self.mocked_session_key = mocked_session_key
        self.mocked_unionid = mocked_unionid
        super().__init__(*args, **kwargs)

    @call_validate
    def mock_success(self, request=None, context=None):
        return dict(
            openid=self.mocked_openid or str(uuid.uuid4()),
            session_key=self.mocked_session_key or str(uuid.uuid4()),
            unionid=self.mocked_unionid or str(uuid.uuid4()),
        )

    @call_validate
    def mock_invalid_code(self, request=None, context=None):
        return WX_ERRORS['INVALID_CODE']

    def _validate_code(self, query):
        if f"js_code={self.code}" in query:
            return True
        else:
            return False

    def mock_callback(self, request=None, context=None):
        if self._validate_code(request.query):
            return self.mock_success(request, context)
        else:
            return self.mock_invalid_code(request, context)


class WXWebCode2AccessTokenCallback(WXCode2SessionCallback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = str(uuid.uuid4())
        self.refresh_token = str(uuid.uuid4())
        self.openid = str(uuid.uuid4())

    @call_validate
    def mock_success(self, request=None, context=None):
        return dict(
            access_token=self.access_token,
            expires_in=7200,
            refresh_token=self.refresh_token,
            openid=self.openid,
            scope='SCOPE',
        )

    def _validate_code(self, query):
        if f"code={self.code}" in query:
            return True
        else:
            return False


class WXAccessToken2InfoCallback(BaseCallback):
    def __init__(self, access_token, openid, unionid=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = access_token
        self.openid = openid
        self.unionid = unionid or str(uuid.uuid4())

    @call_validate
    def mock_success(self, request=None, context=None):
        return dict(
            openid=self.openid,
            nickname='wechat nick name',
            sex='1',
            province='province',
            city='city',
            country='country',
            headimgurl='http://t2.hddhhn.com/uploads/tu/201610/198/hkgip2b102z.jpg',
            privilege=["PRIVILEGE1" "PRIVILEGE2"],
            unionid=self.unionid,
        )

    @call_validate
    def mock_invalid_openid(self, reqeust=None, context=None):
        return WX_ERRORS['INVALID_OPENID']

    @call_validate
    def mock_invalid_access_token(self, request=None, context=None):
        return WX_ERRORS['INVALID_ACCESS_TOKEN']

    def _validate(self, query):
        if f"access_token={self.access_token}" not in query:
            return 'invalid_access_token'

        if f"openid={self.openid}" not in query:
            return 'invalid_openid'

        return 'success'

    def mock_callback(self, request=None, context=None):
        return getattr(self, f'mock_{self._validate(request.query)}')(request, context)
