# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from common.payment.util import generate_serial_number, PayChannelContext


class UtilTestCases(TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

    def test_generate_serial_number(self):
        sn = generate_serial_number()
        assert len(sn) == 32

    def test_pay_channel_context(self):
        with PayChannelContext(0):
            assert PayChannelContext.get_pay_channel() == 0

        assert PayChannelContext.get_pay_channel() is None
