# -*- coding: utf-8 -*-
#       File: routing.py
#    Project: simple
#     Author: Tian Xu
#     Create: 18-7-16
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from channels.routing import ProtocolTypeRouter, URLRouter
from ws_service import routing as ws_routing
from ws_service.middlewares import AuthTokenMiddleware


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthTokenMiddleware(
        URLRouter(
            ws_routing.websocket_urlpatterns
        )
    ),
})
