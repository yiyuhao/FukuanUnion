#
#      File: baidu.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
from urllib.parse import urlencode

import requests
from requests import RequestException

from common.utils import RedisUtil
from config import BaiduVoiceSynthesisConfig as Conf

logger = logging.getLogger(__name__)


class BaiduApiError(Exception):
    pass


class BaiduApi:
    """
        百度 语音合成use case
        https://ai.baidu.com/docs#/TTS-API/top
    """

    @staticmethod
    def get_token():
        params = {'grant_type': 'client_credentials',
                  'client_id': Conf.api_key,
                  'client_secret': Conf.secret_key}
        post_data = urlencode(params)
        post_data = post_data.encode('utf-8')
        try:
            response = requests.post(Conf.token_url, post_data)
            result = response.json()
            logger.debug(f'fetch baidu token response: {result}')
        except (RequestException, ValueError) as e:
            logger.error(f'fetch baidu token failed: {e}')
            raise BaiduApiError(f'fetch baidu token failed: {e}')

        if 'access_token' not in result.keys() and 'scope' not in result.keys():
            raise BaiduApiError('MAYBE API_KEY or SECRET_KEY not correct: '
                                'access_token or scope not found in token response')

        if 'audio_tts_post' not in result['scope'].split(' '):  # 有此scope表示有tts能力，没有请在网页里勾选
            raise BaiduApiError('scope is not correct')

        return result['access_token'], result['expires_in']


def get_baidu_token():
    """一般30天有效"""
    token = RedisUtil.get_access_token('baidu_voice_access_token')
    error = None

    if not token:
        try:
            token, expires_in = BaiduApi.get_token()
            RedisUtil.set_access_token('baidu_voice_access_token', token, expires_in - 60 * 60)  # 预留部分时间
        except BaiduApiError as e:
            logger.error(f'baidu error: {e.message}')
            error = e.message

    return token, error
