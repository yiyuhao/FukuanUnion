# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework.reverse import reverse

import config
from common.auth.internal.validate_util import TokenGenerate
from test.auto_test.steps.base import BaseStep


class SharedPaySteps(BaseStep):
    def __init__(self, client_token):
        super().__init__()
        self.client_token = client_token

    def poll_result(self, payment_serial_number, longitude, latitude, accuracy):
        url = reverse('orders_poll_result')
        resp = self.client.post(url, data=dict(
            payment_serial_number=payment_serial_number,
            longitude=longitude,
            latitude=latitude,
            accuracy=accuracy
        ), format='json')
        return resp.json()

    def unfreeze_immediately(self):
        backup = config.PAYMENT_FROZEN_TIME
        config.PAYMENT_FROZEN_TIME = 0

        url = reverse('payment_unfreeze')
        self.client.credentials(HTTP_ACCESS_TOKEN=self.client_token)
        data = TokenGenerate('TXLcqm9eMxH5agyHnXmLFappbDfzYy4u',
                             'refresh_token').get_token_params()
        resp = self.client.post(url,
                                data=data,
                                format='json')

        config.PAYMENT_FROZEN_TIME = backup
        return resp.json()
