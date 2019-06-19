# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import redis

from dynaconf import settings as dynasettings

#  公众号回复相关config
WEChAT_REPLY_CONFIG = {
    "user": {
        "app_id": dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_USER,
        "app_secret": dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_USER,
        "token": dynasettings.SUBSCRIPTION_ACCOUNT_TOKEN_USER
        # "token": ""
    },
    "merchant": {
        "app_id": dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MERCHANT,
        "app_secret": dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_MERCHANT,
        "token": dynasettings.SUBSCRIPTION_ACCOUNT_TOKEN_MERCHANT
        # "token": ""
    },
    'marketer': {
        "app_id": dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MARKETER,
        "app_secret": dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_MARKETER,
        "token": dynasettings.SUBSCRIPTION_ACCOUNT_TOKEN_MARKETER
        # "token": ""
    }
}

URL_CONFIG = {
    "user": "appid={0}&secret={1}".format(WEChAT_REPLY_CONFIG['user']['app_id'],
                                          WEChAT_REPLY_CONFIG['user']['app_secret']),
    "merchant": "appid={0}&secret={1}".format(WEChAT_REPLY_CONFIG['merchant']['app_id'],
                                              WEChAT_REPLY_CONFIG['merchant']['app_secret']),
    "marketer": "appid={0}&secret={1}".format(WEChAT_REPLY_CONFIG['marketer']['app_id'],
                                              WEChAT_REPLY_CONFIG['marketer']['app_secret'])
}

# 小程序相关
WEChAT_MINI_PROGRAM = {
    "user": {
        "app_id": dynasettings.CLIENT_MINI_APP_ID,
        "app_secret": dynasettings.CLIENT_MINI_APP_SECRET,
    },
    "merchant": {
        "app_id": dynasettings.MERCHANT_MINA_APP_ID,
        "app_secret": dynasettings.MERCHANT_MINA_APP_SECRET,
    },
    'marketer': {
        "app_id": dynasettings.MARKETER_MINA_APP_ID,
        "app_secret": dynasettings.MARKETER_MINA_APP_SECRET,
    }
}
