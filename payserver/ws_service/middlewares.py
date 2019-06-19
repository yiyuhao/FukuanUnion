# -*- coding: utf-8 -*-
#       File: middlewares.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-18
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
from urllib.parse import parse_qs

from django.core.cache import cache
from rest_framework import exceptions


logger = logging.getLogger(__name__)


class AuthTokenMiddleware(object):
    """
    Custom middleware (insecure) that takes token from the headers.
    """

    def __init__(self, inner):
        # Store the ASGI application we were passed
        self.inner = inner

    def __call__(self, scope):
        # 验证 token
        token = parse_qs(scope.get('query_string', b'').decode()).get('token')
        if token:
            token = token[0]

        if cache.get(token) is None:
            raise exceptions.AuthenticationFailed('Invalid token')
        logger.info(f"This token of ws: {token}")
        return self.inner(scope)
