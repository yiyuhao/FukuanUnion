# -*- coding: utf-8 -*-
#       File: routing.py
#    Project: simple
#     Author: Tian Xu
#     Create: 18-7-16
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.conf.urls import url

from ws_service import consumers


websocket_urlpatterns = [
    url(r'^ws/ws-service/(?P<channel_key>[^/]+)/$', consumers.WeChatAuthConsumer),
]
