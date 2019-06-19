#      File: utils.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from .config import WechatHttpApiConfig as Conf
from .http_api import code_to_session

logger = logging.getLogger(__name__)


def get_openid(app_id, app_secret, code):
    """
    :param app_id: wechat mina app_id
    :param app_secret: wechat mina app_secret
    :param code: wechat login code
    :return: (tuple)  openid, unionid, session_key
    """
    resp_json = code_to_session(appid=app_id, secret=app_secret, js_code=code,
                                grant_type=Conf.grant_type)

    openid = resp_json.get('openid')
    session_key = resp_json.get('session_key')
    unionid = resp_json.get('unionid')

    if openid and session_key and unionid:
        return openid, unionid, session_key

    # {"errcode":40163,"errmsg":"code been used, hints: [ req_id: NYr0eA0702hb33 ]"}
    logger.error('get wechat openid error, resp: {}'.format(resp_json))
    return None, None, None


def json_hook(resp):
    resp.json = resp.json()
