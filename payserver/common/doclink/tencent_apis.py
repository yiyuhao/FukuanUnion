#!/usr/bin/python3
#
#   Project: payunion
#    Author: Tian Xu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging

import requests

from config import TENCENT_MAP_KEY
from .exceptions import ApiRequestError, ApiStatusCodeError

logger = logging.getLogger(__name__)


def fetch_adcode(adcode):
    """
    下载adcode的信息
    :param adcode: 腾讯地图的adcode
    :return:
    """
    url = 'https://apis.map.qq.com/ws/district/v1/search'
    params = {
        'key': TENCENT_MAP_KEY,
        'keyword': adcode
    }
    resp = requests.get(url=url, params=params)
    if resp.status_code not in (200, 201):
        logger.error(f'Fetching the adcode: {adcode} error. '
                     f'Status code: {resp.status_code}')

        raise ApiStatusCodeError(resp.status_code)

    resp_json = resp.json()
    if not resp_json['result']:
        logger.error(f'Fetching the adcode: {adcode} error. '
                     f'Response json: {resp_json}')
        raise ApiRequestError(resp_json)

    item = resp_json['result'][0][0]
    return item
