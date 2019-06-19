# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.contrib.sessions.backends.base import UpdateError
from django.core.exceptions import SuspiciousOperation
from django.middleware.csrf import CsrfViewMiddleware, get_token

from config import ALLOWED_ORIGINS
from .token_store import TokenStore


class ForceEnableCsrfCookieMiddleware(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return None

    def process_view(self, request, callback, callback_args, callback_kwargs):
        retval = super().process_view(request, callback, callback_args, callback_kwargs)
        # Force process_response to send the cookie
        get_token(request)
        return retval


def token_middleware(get_response):
    def middleware(request):
        # process request
        token = request.META.get('HTTP_ACCESS_TOKEN')
        token_session = TokenStore(token)
        request.token_session = token_session

        response = get_response(request)

        # process response
        try:
            accessed = token_session.accessed
            modified = token_session.modified
            empty = token_session.is_empty()
        except AttributeError:
            pass
        else:
            if accessed:
                if modified and not empty:
                    if response.status_code != 500:
                        try:
                            request.token_session.save()
                        except UpdateError:
                            raise SuspiciousOperation(
                                "The request's token session was deleted before the "
                                "request completed. The user may have logged "
                                "out in a concurrent request, for example."
                            )
        return response

    return middleware


def cors_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        origin = request.META.get('HTTP_ORIGIN')
        if origin in ALLOWED_ORIGINS:
            response.__setitem__('Access-Control-Allow-Origin', origin)
            response.__setitem__("Access-Control-Allow-Methods",
                                 "GET, POST, OPTIONS")
            response.__setitem__("Access-Control-Allow-Credentials", "true")
            response.__setitem__("Access-Control-Allow-Headers",
                                 "Origin, No-Cache, X-Requested-With, Access-Token, "
                                 "If-Modified-Since, Pragma, Last-Modified, "
                                 "Cache-Control, Expires, Content-Type, X-E4M-With, X-CSRFToken")
            return response
        return response

    return middleware
