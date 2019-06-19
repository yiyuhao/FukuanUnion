#      File: login.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/19
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
import uuid

from django.core.cache import cache
from dynaconf import settings as dynasettings

from common.doclink.utils import get_openid
from common.model_manager.merchant_admin_manager import MerchantAdminModelManager
from config import MerchantMiniProgram
from common.error_handler import MerchantError

logger = logging.getLogger(__name__)


class LoginError(Exception):
    def __init__(self, message):
        super(LoginError, self).__init__(message)
        self.message = message
        logger.error(message)


class LoginHandlerBase:
    """
        see https://developers.weixin.qq.com/miniprogram/dev/api/api-login.html
    """

    def __init__(self):

        self.code = None
        self.openid = None
        self.session_key = None
        self.token = None

        # 子类必须设置以下属性
        self.app_id = None
        self.app_secret = None
        self.user_token_expiration_time = None

    def _get_openid(self):
        self.openid, self.unionid, self.session_key = get_openid(
            app_id=self.app_id,
            app_secret=self.app_secret,
            code=self.code
        )
        if self.openid:
            return self.openid, self.unionid, self.session_key
        else:
            raise LoginError(MerchantError.get_openid_error['error_code'])

    def _check_user_existed(self):
        """
            通过self.openid判断用户是否存在, 不存在时raise LoginError
            客户端不需要check user时, 不用重写该方法
            :return: None
        """
        pass

    def _cache_token(self):
        # 创建token
        self.token = str(uuid.uuid4())
        user = dict(
            openid=self.openid,
            unionid=self.unionid,
            session_key=self.session_key,
        )
        # 创建或刷新token过期时间
        cache.set(self.token, user, self.user_token_expiration_time)

        logger.info('cached user(expired in {}s): dict({}={})'.format(
            self.user_token_expiration_time, '{}***'.format(self.token[:5]), user
        ))

    def login(self, code):
        self.code = code

        #  请求微信登录API获取openid + session_key 失败raise LoginError
        self._get_openid()

        #  检查用户是否已绑定
        self._check_user_existed()

        #  redis存储token={'token_BALABALA': {'openid': '...', 'session_key': '...'}}
        self._cache_token()

        #  返回token
        return self.token


class MerchantLoginHandler(LoginHandlerBase):
    def __init__(self):
        super(MerchantLoginHandler, self).__init__()
        self.app_id = dynasettings.MERCHANT_MINA_APP_ID
        self.app_secret = dynasettings.MERCHANT_MINA_APP_SECRET
        self.user_token_expiration_time = MerchantMiniProgram.user_token_expiration_time

    def _check_user_existed(self):
        manager = MerchantAdminModelManager()
        user = manager.get_merchant_admin(self.unionid)
        if not user:
            raise LoginError(MerchantError.user_is_not_a_merchant_admin['error_code'])
        return user

    @property
    def user(self):
        return self._check_user_existed()
