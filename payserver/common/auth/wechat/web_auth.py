# -*- coding: utf-8 -*-
#       File: web_auth.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-8-1
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import json
import requests
from requests.exceptions import RequestException


class WeChantWebAuthHandler(object):
    """
    微信网页授权
    先获取到
    """

    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret

    def gen_access_token(self, code):
        """
        根据code获取 access_token
        :param code: 授权获取的code
        :return:
        """
        url = ('https://api.weixin.qq.com/sns/oauth2/access_token?appid={appid}&'
                                'secret={secret}&code={code}&grant_type=authorization_code'.format(
            appid=self.app_id, secret=self.app_secret, code=code))

        resp = requests.get(url=url)
        try:
            resp_json = resp.json()
        except (ValueError, RequestException):
            resp_json = {}

        access_token = resp_json.get('access_token')
        # refresh_token = resp_json.get('refresh_token')
        openid = resp_json.get('openid')
        return access_token, openid

    def gen_user_info(self, access_token, openid):
        """
        根据access_token， openid获取用户信息
        :param access_token: access_token
        :param code: 用户授权零时code
        :param openid: openid
        :return:
        """
        url = ('https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}'
                         '&lang=zh_CN'.format(access_token=access_token, openid=openid))

        resp = requests.get(url=url)
        try:
            resp_json = resp.json()
            resp_json_str = json.dumps(resp_json, ensure_ascii=False).encode('raw-unicode-escape').decode("utf-8")
            resp_json = json.loads(resp_json_str)
        except (ValueError, RequestException):
            resp_json = {}

        return resp_json
