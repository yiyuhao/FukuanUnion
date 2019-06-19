from common.auth.wechat.login import LoginHandlerBase
from marketer.config import MARKETER_MINI_PROGRAM
from common.model_manager.marketer_manager import MarketerModelManager
from dynaconf import settings as dynasettings


class MarketerLoginHandler(LoginHandlerBase):
    """
     Marketer login handler
    """
    def __init__(self):
        super().__init__()
        self.app_id = dynasettings.MARKETER_MINA_APP_ID
        self.app_secret = dynasettings.MARKETER_MINA_APP_SECRET
        self.user_token_expiration_time = MARKETER_MINI_PROGRAM.user_token_expiration_time

    def _check_user_existed(self):
        manager = MarketerModelManager()
        user = manager.has_unionid(self.unionid)
        return user

    def login(self, code):
        self.code = code
        self._get_openid()
        self._cache_token()
        return self.token


