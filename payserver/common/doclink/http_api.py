#      File: http_api.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from doclink import Consumer

from .config import WechatHttpApiConfig as Conf

consumer = Consumer(Conf.base_url, expected_status_code=200)


@consumer.resp_hook
def json_hook(resp):
    resp.json = resp.json()


@consumer.get(Conf.code_to_session)
def code_to_session(resp):
    """Exchange access_token from auth code.

    Ags:
        appid (str): wechat mini program app id
        secret (str): app secret
        js_code (str): 登录时获取的 code
        grant_type (str): 填写为'authorization_code'

    Returns:
        dict: openid, session_key.

    <meta>
        args:
            query:
                - appid
                - secret
                - js_code
                - grant_type
    </meta>
    """
    return resp.json
