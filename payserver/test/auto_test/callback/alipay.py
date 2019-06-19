#!/usr/bin/python3
#
#   Project: payunion
#    Author: Tian Xu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid

from faker import Faker

from test.auto_test.callback.base import BaseCallback, call_validate

fake = Faker('zh_CN')

ALIPAY_ERRORS = {
    'INVALID_CODE': {'errcode': 40029, 'errmsg': 'invalid code'},
    'INVALID_ACCESS_TOKEN': {"errcode": 40014, "errmsg": 'invalid access token'}
}


class AlipayCode2AccessTokenCallback(BaseCallback):
    """ Alipay 通过code换取access_token """

    def __init__(self, code, mocked_user_id=None, *args, **kwargs):
        self.code = code
        self.mocked_user_id = mocked_user_id
        self.access_token = kwargs.get('access_token', None) or uuid.uuid4().hex
        super().__init__(*args, **kwargs)

    @call_validate
    def mock_success(self, request=None, context=None):
        return {
            'alipay_system_oauth_token_response': {
                "access_token": "authbseb" + self.access_token,
                "alipay_user_id": self.mocked_user_id or "2088102176283877",
                "expires_in": 1296000,
                "re_expires_in": 31536000,
                "refresh_token": "authbseb" + uuid.uuid4().hex,
                "user_id": self.mocked_user_id or "2088102176283877"
            },
            'sign': fake.pystr(min_chars=128, max_chars=128)
        }

    @call_validate
    def mock_invalid_code(self, request=None, context=None):
        return ALIPAY_ERRORS['INVALID_CODE']

    def _validate_code(self, query):
        if f"code={self.code}" in query:
            return True
        else:
            return False

    def mock_callback(self, request=None, context=None):
        if self._validate_code(request.query):
            return self.mock_success(request, context)
        else:
            return self.mock_invalid_code(request, context)


class AlipayAccessToken2InfoCallback(BaseCallback):
    def __init__(self, access_token, user_id=None, nick_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = access_token
        self.user_id = user_id or '2088102104794936'
        self.nick_name = nick_name or 'alipay nickname'

    @call_validate
    def mock_success(self, request=None, context=None):
        return {
            "alipay_user_info_share_response": {
                "code": "10000",
                "msg": "Success",
                "user_id": self.user_id,
                "avatar": "http://tfsimg.alipay.com/images/partner/XXX",
                "province": "安徽省",
                "city": "安庆",
                "nick_name": self.nick_name,
                "is_student_certified": "T",
                "user_type": "1",
                "user_status": "T",
                "is_certified": "T",
                "gender": "F"
            },
            "sign": "ERITJKEIJKJHKKKKKKKHJEREEEEEEEEEEE"
        }

    @call_validate
    def mock_invalid_access_token(self, request=None, context=None):
        return ALIPAY_ERRORS['INVALID_ACCESS_TOKEN']

    def _validate(self, query):
        if f"auth_token={self.access_token.replace(' ', '+')}" not in query:
            return 'invalid_access_token'

        return 'success'

    def mock_callback(self, request=None, context=None):
        return getattr(self, f'mock_{self._validate(request.query)}')(
            request, context)
