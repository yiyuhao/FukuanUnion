# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import time
import requests

from dynaconf import settings as dynasettings

from requests.exceptions import RequestException
from common.auth.internal.validate_util import TokenGenerate
from padmin.subscription_account_reply.const import URL_CONFIG
from common.utils import RedisUtil


class RefreshTokenUtil(object):

    @classmethod
    def __access_wechat_to_refresh_token(cls, params):
        # 请求微信获取access_token
        account_type = params.pop('account_type', None)  # user, merchant, marketer
        if account_type not in ['user', 'merchant','marketer',]:
            return {"detail": "refresh_failed", "errmsg": "invalid params"}

        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&{}".format(
            URL_CONFIG[account_type]
        )
        access_token = None
        retry = 1
        resp_json = {"detail": "refresh_failed", "errmsg": "refresh_failed"}
        while retry <= 3:
            try:
                resp = requests.get(url)
                resp_json = resp.json()
                access_token = resp_json["access_token"]

            except (RequestException, KeyError, ValueError) as e:
                retry = retry + 1
                time.sleep(1)

            else:
                break

        if resp_json.get('errmsg') is None and access_token is not None:
            # 刷新redis中access_token
            key = "subscription_account_access_token_{}".format(account_type)
            RedisUtil.set_access_token(key, access_token)
            return {"detail": "refresh_ok", "errmsg": ""}

        return {"detail": "refresh_failed", "errmsg": resp_json.get('errmsg')}

    @classmethod
    def __access_internal_to_refresh_token(cls, params):
        url = None
        if dynasettings.ENV == 'test':
            url = "http://api.mishitu.com/api/admin/wechat/access_token/obtain"
        elif dynasettings.ENV == 'dev':
            url = "http://api-alpha.mishitu.com/api/admin/wechat/access_token/obtain"
        if not url:
            return {"detail": "refresh_failed", "errmsg": "invalid params"}
        account_type = params.pop('account_type', None)  # user, merchant, marketer
        if account_type not in ['user', 'merchant', 'marketer', ]:
            return {"detail": "refresh_failed", "errmsg": "invalid params"}

        req_data = TokenGenerate(dynasettings.INTERNAL_AUTH_TOKEN_CONFIG_REFRESH_TOKEN, 'refresh_token').get_token_params()
        try:
            resp = requests.post(url, json=req_data)
            resp_json = resp.json()
            key = "subscription_account_access_token_{}".format(account_type)
            RedisUtil.set_access_token(key, resp_json[account_type])
            return {"detail": "refresh_ok", "errmsg": ""}
        except (RequestException, KeyError, ValueError) as e:
           return  {"detail": "refresh_failed", "errmsg": repr(e)}


    @classmethod
    def refresh_token(cls, params):
        if dynasettings.ENV == 'prod':
            return cls.__access_wechat_to_refresh_token(params)

        return cls.__access_internal_to_refresh_token(params)


