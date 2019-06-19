# -*- coding: utf-8 -*-
import os
import logging

import requests

from timer_common import TokenGenerate

logging.basicConfig(level = logging.INFO,format = '%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def payment_unfreezent(url):
    data = TokenGenerate('TXLcqm9eMxH5agyHnXmLFappbDfzYy4u', 'refresh_token').get_token_params()
    resp = requests.post(url, json=data)
    resp_json = resp.json()
    logger.info("payment_unfreeze, occur time is {}, response result is {} ".format(data['timestamp'], resp_json))


def handler(event, context):
    env = os.environ['env']
    version = os.environ['version']

    url_map = {
        'test': "http://api-alpha.mishitu.com/api/user/{}/payment/unfreeze".format(version),
        'prod': "http://api.mishitu.com/api/user/{}/payment/unfreeze".format(version)
    }
    payment_unfreezent(url_map[env])
