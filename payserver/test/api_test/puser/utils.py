# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from common.token_store import TokenStore
from puser.consts import client_session_key


class ClientLoggedInMixin(object):
    def setUp(self):
        if hasattr(self, 'test_client'):
            token_session = TokenStore(namespace='client')
            token_session.create()
            token_session[client_session_key] = self.test_client.id
            token_session.save()
            self.token = token_session.token
            self.client.credentials(HTTP_ACCESS_TOKEN=self.token)
