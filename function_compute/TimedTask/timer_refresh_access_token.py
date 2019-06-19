# -*- coding: utf-8 -*-
import os
import logging

import requests

from timer_common import TokenGenerate

logging.basicConfig(level = logging.INFO,format = '%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def to_refresh_token(account_type, url):
    """
    定时刷新公众号refresh_token
    :param account_type:
    :return:
    """

    token = 'TXLcqm9eMxH5agyHnXmLFappbDfzYy4u'
    key_type = 'refresh_token'
    retry = 1
    while retry <= 3:
        data = TokenGenerate(token, key_type).get_token_params()
        data.update({'account_type': account_type}) # user, merchant, marketer
        resp = requests.post(url, json=data)
        resp_json = resp.json()
        logger.info("refresh {} access_token, occur time is {}, response result is {} ".format(account_type, data['timestamp'], resp_json))
        if resp_json.get("detail") == "refresh_ok":
            break
        retry = retry + 1


def refresh_handler(event, context):
    env = os.environ['env']
    url_map = {
        'test': "http://api-alpha.mishitu.com/api/admin/wechat/access_token/refresh",
        'prod': "http://api.mishitu.com/api/admin/wechat/access_token/refresh"
    }

    to_refresh_token('user', url_map[env])
    to_refresh_token('merchant', url_map[env])
    to_refresh_token('marketer', url_map[env])

