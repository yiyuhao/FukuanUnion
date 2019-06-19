#      File: config.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class WechatHttpApiConfig:
    base_url = 'https://api.weixin.qq.com/'
    code_to_session = 'sns/jscode2session'

    grant_type = 'authorization_code'
