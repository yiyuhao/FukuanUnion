#      File: exceptions.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/6
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class InvalidStatusError(Exception):
    pass


class BalanceInsufficient(Exception):
    """提现余额不足"""
    pass
