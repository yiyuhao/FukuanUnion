# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from dynaconf import settings as dynasettings

TOKEN_CONFIG = {
    "refresh_token": dynasettings.INTERNAL_AUTH_TOKEN_CONFIG_REFRESH_TOKEN,
}