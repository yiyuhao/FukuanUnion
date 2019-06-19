# -*- coding: utf-8 -*-
import os
import logging

import requests

from timer_common import TokenGenerate

logging.basicConfig(level = logging.INFO,format = '%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def send_merchant_month_bill(url):
    data = TokenGenerate('TXLcqm9eMxH5agyHnXmLFappbDfzYy4u', 'refresh_token').get_token_params()
    resp = requests.post(url, json=data)
    resp_json = resp.json()
    logger.info("send_merchant_month_bill, occur time is {}, response result is {} ".format(data['timestamp'], resp_json))


def handler(event, context):
    env = os.environ['env']
    url_map = {
        'test': "http://api-alpha.mishitu.com/api/admin/wechat/push_merchant_month_bill",
        'prod': "http://api.mishitu.com/api/admin/wechat/push_merchant_month_bill"
    }
    send_merchant_month_bill(url_map[env])
