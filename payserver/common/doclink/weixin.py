# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from doclink import Consumer

from . import utils


auth_consumer = Consumer('https://api.weixin.qq.com/sns/')

auth_consumer.resp_hook(utils.json_hook)


@auth_consumer.get('jscode2session')
def jscode2session(resp):
    """
    <meta>
        args:
            query:
                - appid
                - secret
                - js_code
                - grant_type: authorization_code
        expected_status_code: 200
    </meta>
    """
    return resp.json
