# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from dynaconf import settings as dynasettings

appid = dynasettings.CLIENT_MINI_APP_ID
app_secret = dynasettings.CLIENT_MINI_APP_SECRET
token_namespace = 'client'
client_session_key = 'client_id'

alipay_appid = dynasettings.ALIPAY_APP_ID

if dynasettings.IS_DEBUG:
    alipay_api_gateway = 'https://openauth.alipaydev.com'
else:
    alipay_api_gateway = 'https://openauth.alipay.com'