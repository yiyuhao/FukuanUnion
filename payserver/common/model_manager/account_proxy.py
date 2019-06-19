# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from common.models import Account
from common.payment.util import PayChannelContext
from config import PAY_CHANNELS


class AccountProxy(Account):
    class Meta:
        proxy = True

    @property
    def channel_balance(self):
        pay_channel = PayChannelContext.get_pay_channel()
        if pay_channel == PAY_CHANNELS.WECHAT:
            return self.balance
        elif pay_channel == PAY_CHANNELS.ALIPAY:
            return self.alipay_balance
        else:
            raise ValueError("Don't know the current pay channel")

    @channel_balance.setter
    def channel_balance(self, value):
        pay_channel = PayChannelContext.get_pay_channel()
        if pay_channel == PAY_CHANNELS.WECHAT:
            self.balance = value
        elif pay_channel == PAY_CHANNELS.ALIPAY:
            self.alipay_balance = value
        else:
            raise ValueError("Don't know the current pay channel")

    @property
    def channel_withdrawable_balance(self):
        pay_channel = PayChannelContext.get_pay_channel()
        if pay_channel == PAY_CHANNELS.WECHAT:
            return self.withdrawable_balance
        elif pay_channel == PAY_CHANNELS.ALIPAY:
            return self.alipay_withdrawable_balance
        else:
            raise ValueError("Don't know the current pay channel")

    @channel_withdrawable_balance.setter
    def channel_withdrawable_balance(self, value):
        pay_channel = PayChannelContext.get_pay_channel()
        if pay_channel == PAY_CHANNELS.WECHAT:
            self.withdrawable_balance = value
        elif pay_channel == PAY_CHANNELS.ALIPAY:
            self.alipay_withdrawable_balance = value
        else:
            raise ValueError("Don't know the current pay channel")
