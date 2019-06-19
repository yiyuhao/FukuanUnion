# -*- coding: utf-8 -*-
#       File: config.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-24
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from redis import ConnectionPool
from dynaconf import settings as dynasettings


APP_ID = dynasettings.RLYSMS_APP_ID
ACCOUNT_SID = dynasettings.RLYSMS_ACCOUNT_SID
AUTH_TOKEN = dynasettings.RLYSMS_AUTH_TOKEN
BASE_URL = 'https://app.cloopen.com:8883'

CODE_RANGE = (100000, 999999)
VERIFY_CODE_EXPIRES_IN = 10   # 分钟
RECORD_EXPIRES_IN = 10  # 分钟

TEMPLATE_ID = 314844   # 短信模板

REDIS_URL = 'redis://{0}{1}:{2}/{3}'.format(
    ':%s@' % dynasettings.REDIS_PASSWORD if dynasettings.REDIS_PASSWORD else '',  # noqa
    dynasettings.REDIS_HOST,
    dynasettings.as_int('REDIS_PORT'),
    3
)

redis_pool = ConnectionPool.from_url(REDIS_URL)

ERROR_MSG = {
    '000000': '验证码发送成功',
    '160014': '短信通道余额不足',
    '160032': '短信模板无效',
    '160034': '号码黑名单',
    '160036': '短信模板类型未知',
    '160038': '短信验证码发送过频繁',
    '160039': '发送数量超出同模板同号天发送次数上限',
    '160040': '验证码超出同模板同号码天发送上限',
    'FREQUENTLY': '发送短信过于频繁, 请间隔60s重试',
    'PHONEERR': '请确认电话号码是否正确',
    'DEFAULT': '验证码发送失败',
}