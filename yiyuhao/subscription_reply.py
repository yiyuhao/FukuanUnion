# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
import random
import string
import time
import hashlib
import requests

from dynaconf import settings as dynasettings

REFRESH_TOKEN = dynasettings.INTERNAL_AUTH_TOKEN_CONFIG_REFRESH_TOKEN

logging.basicConfig(level = logging.INFO,format = '%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class TokenGenerate(object):
    def __init__(self, token, key_type):
        self.token = token
        self.key_type = key_type

    def get_token_params(self):
        time_stamp = int(time.time())
        random_key = ''.join(random.sample(string.ascii_letters + string.digits, 32))
        key_type = self.key_type
        token = self.token

        param_list = [token, str(time_stamp), random_key, key_type]
        param_list.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(param_list).encode('utf-8'))
        signature = sha1.hexdigest()

        data = {
            'timestamp': time_stamp,
            'key': random_key,
            'signature': signature,
            'key_type': key_type
        }
        return data


def to_refresh_token(account_type):
    """
    定时刷新公众号refresh_token
    :param account_type:
    :return:
    """

    url = "http://localhost:8000/adminapi/wechat/access_token/refresh"

    token = REFRESH_TOKEN
    key_type = 'refresh_token'
    token_generator = TokenGenerate(token, key_type)
    retry = 1
    while retry <= 3:
        data = token_generator.get_token_params()
        data.update({'account_type': account_type}) # user, merchant, marketer
        resp = requests.post(url, json=data)
        resp_json = resp.json()
        logger.info("refresh {} access_token, occur time is {}, response result is {} ".
                    format(account_type, data['timestamp'], resp_json))
        if resp_json.get("detail") == "refresh_ok":
            break
        retry = retry + 1


if __name__ == "__main__":
    to_refresh_token('user')
    to_refresh_token('merchant')
    to_refresh_token('marketer')
