#      File: util.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


import random
import threading

from django.utils import timezone


def generate_serial_number():
    return timezone.now().strftime('%Y%m%d%H%M%S%f') + ('%012d' % random.randint(0, 999999999999))


class PayChannelContext(object):
    thread_local = threading.local()

    def __init__(self, pay_channel):
        self.pay_channel = pay_channel

    def __enter__(self):
        self.thread_local.pay_channel = self.pay_channel

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.thread_local.pay_channel = None

    @classmethod
    def get_pay_channel(cls):
        return getattr(cls.thread_local, 'pay_channel', None)
